from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Tuple

import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from poliastro.bodies import Sun, Earth
from poliastro.twobody import Orbit
from poliastro.ephem import get_body_barycentric_posvel

from .config import settings
from .models import Observation
import logging

logger = logging.getLogger(__name__)


def _observation_to_heliocentric_vector(obs: Observation, distance_au: float) -> Tuple[np.ndarray, datetime]:
    sky = SkyCoord(
        ra=obs.ra_hours * u.hourangle,
        dec=obs.dec_degrees * u.deg,
        distance=distance_au * u.AU,
        frame="icrs",
    )
    comet_vec = sky.cartesian.xyz.to(u.km).value
    obs_time = Time(obs.observation_time, scale="utc")

    earth_state = get_body_barycentric_posvel("earth", obs_time)
    earth_vec = earth_state[0].xyz.to(u.km).value
    heliocentric_vec = earth_vec + comet_vec
    return heliocentric_vec, obs_time


def derive_orbit(observations: Iterable[Observation]) -> Orbit:
    obs_list: List[Observation] = sorted(observations, key=lambda o: o.observation_time)
    if len(obs_list) < 3:
        raise ValueError("At least 3 observations are required to derive an orbit.")

    base_distance = 0.8
    vectors = []
    times = []
    for idx, obs in enumerate(obs_list):
        distance = base_distance + 0.02 * idx
        state_vec, obs_time = _observation_to_heliocentric_vector(obs, distance)
        vectors.append(state_vec)
        times.append(obs_time)

    time_seconds = np.array([(t - times[0]).to(u.s).value for t in times])
    positions = np.vstack(vectors)

    coeffs = []
    for axis in range(3):
        coeff = np.polyfit(time_seconds, positions[:, axis], 1)
        coeffs.append(coeff)

    mid_idx = len(obs_list) // 2
    t_mid = time_seconds[mid_idx]
    position = np.array([np.polyval(coeffs[axis], t_mid) for axis in range(3)]) * u.km
    velocity = np.array([coeffs[axis][0] for axis in range(3)]) * (u.km / u.s)
    epoch = times[mid_idx]

    orbit = Orbit.from_vectors(Sun, position, velocity, epoch=epoch)
    return orbit


def find_closest_approach(orbit: Orbit) -> Tuple[datetime, float, float]:
    start_time = orbit.epoch
    days = settings.sample_propagation_days
    offsets = np.linspace(0, days, days + 1) * u.day

    min_distance = float("inf")
    min_time = start_time
    rel_speed = 0.0

    for offset in offsets:
        current_epoch = start_time + offset
        propagated = None
        # Попытки выполнить propagate; если основной метод падает — попробуем с разными rtol
        try:
            propagated = orbit.propagate(offset)
        except Exception as e:
            logger.warning("Propagation failed for offset %s: %s", offset, e)
            # попробовать несколько значений rtol
            for rtol in (1e-6, 1e-5, 1e-4):
                try:
                    propagated = orbit.propagate(offset, rtol=rtol)
                    logger.info("Propagation succeeded for offset %s with rtol=%s", offset, rtol)
                    break
                except Exception as e2:
                    logger.debug("Propagation retry rtol=%s failed: %s", rtol, e2)
            # Попробовать численную интеграцию (cowell) как запасной вариант
            for method in ("cowell",):
                try:
                    propagated = orbit.propagate(offset, method=method)
                    logger.info("Propagation succeeded for offset %s with method=%s", offset, method)
                    break
                except Exception as e3:
                    logger.debug("Propagation retry method=%s failed: %s", method, e3)
        if propagated is None:
            # не удалось распространить для этого шага — пропускаем
            logger.warning("Skipping offset %s because propagation failed", offset)
            continue
        comet_r = propagated.r.to(u.km).value
        comet_v = propagated.v.to(u.km / u.s).value

        earth_state = get_body_barycentric_posvel("earth", current_epoch)
        earth_r = earth_state[0].xyz.to(u.km).value
        earth_v = earth_state[1].xyz.to(u.km / u.s).value

        distance = np.linalg.norm(comet_r - earth_r)
        if distance < min_distance:
            min_distance = distance
            min_time = current_epoch
            rel_speed = np.linalg.norm(comet_v - earth_v)

    if min_distance == float("inf"):
        raise RuntimeError("Propagation failed for all sampled times")

    return min_time.to_datetime(), float(min_distance), float(rel_speed)
