"""
Orbit calculation using astropy and scipy.

This module handles:
1. Converting RA/Dec observations to 3D positions
2. Determining orbital elements from observations (simplified method)
3. Finding closest approach to Earth
"""
from datetime import datetime, timedelta
from typing import List, Tuple
import numpy as np

from astropy import units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, solar_system_ephemeris, get_body_barycentric_posvel
from astropy.coordinates import ICRS, GCRS
from scipy.optimize import minimize_scalar

from app.models import Observation
from app.schemas import OrbitElements, ClosestApproach, ComputeResponse


# Physical constants
AU_TO_KM = 1.496e8  # 1 AU in km
EARTH_MU = 3.986004418e5  # Earth's gravitational parameter (km^3/s^2)
SUN_MU = 1.32712440018e11  # Sun's gravitational parameter (km^3/s^2)


def observations_to_vectors(observations: List[Observation]) -> Tuple[List[np.ndarray], List[datetime]]:
    """
    Convert observations (RA, Dec, time) to unit direction vectors.
    
    Returns:
        Tuple of (direction_vectors, times)
    """
    vectors = []
    times = []
    
    for obs in observations:
        # Create SkyCoord from RA/Dec
        coord = SkyCoord(
            ra=obs.ra_hours * u.hour,
            dec=obs.dec_degrees * u.degree,
            frame='icrs'
        )
        
        # Convert to unit vector (cartesian)
        unit_vector = coord.cartesian.xyz.value
        vectors.append(unit_vector)
        times.append(obs.observation_time)
    
    return vectors, times


def simple_orbit_determination(observations: List[Observation]) -> dict:
    """
    Simplified orbit determination from observations.
    Uses statistical approach to estimate orbital elements.
    
    This is a simplified hackathon version. In production, use proper
    orbit determination methods (Gauss, Laplace, etc.)
    """
    direction_vectors, obs_times = observations_to_vectors(observations)
    
    # Get Earth positions at observation times
    earth_positions = []
    for obs_time in obs_times:
        t = Time(obs_time)
        with solar_system_ephemeris.set('builtin'):
            earth_pos, _ = get_body_barycentric_posvel('earth', t)
            earth_positions.append(earth_pos.xyz.to(u.km).value)
    
    earth_positions = np.array(earth_positions)
    
    # Estimate distance to comet (simplified - assume ~3 AU)
    # In real implementation, this would be determined from parallax or other methods
    estimated_distance_km = 3 * AU_TO_KM
    
    # Calculate approximate comet positions
    comet_positions = []
    for i, direction in enumerate(direction_vectors):
        comet_pos = earth_positions[i] + direction * estimated_distance_km
        comet_positions.append(comet_pos)
    
    comet_positions = np.array(comet_positions)
    
    # Calculate center (approximate sun position relative to observations)
    sun_pos = np.array([0, 0, 0])  # Sun at origin in barycentric frame
    
    # Calculate orbital parameters from positions
    # Average distance from sun (semi-major axis)
    distances = np.linalg.norm(comet_positions, axis=1)
    a_km = np.mean(distances)
    a_au = a_km / AU_TO_KM
    
    # Estimate eccentricity from distance variation
    max_dist = np.max(distances)
    min_dist = np.min(distances)
    e = (max_dist - min_dist) / (max_dist + min_dist) if (max_dist + min_dist) > 0 else 0.5
    e = min(max(e, 0.1), 0.95)  # Clamp between 0.1 and 0.95
    
    # Calculate orbital plane normal (simplified)
    if len(comet_positions) >= 3:
        v1 = comet_positions[1] - comet_positions[0]
        v2 = comet_positions[2] - comet_positions[0]
        normal = np.cross(v1, v2)
        normal = normal / np.linalg.norm(normal)
    else:
        normal = np.array([0, 0, 1])
    
    # Calculate inclination (angle between orbital plane and ecliptic)
    ecliptic_normal = np.array([0, 0, 1])
    cos_inc = np.dot(normal, ecliptic_normal)
    inc_rad = np.arccos(np.clip(cos_inc, -1, 1))
    inc_deg = np.degrees(inc_rad)
    
    # Estimate other angles (simplified)
    raan_deg = np.random.uniform(0, 360)  # Simplified
    argp_deg = np.random.uniform(0, 360)  # Simplified
    
    # Estimate time of perihelion (use first observation time)
    perihelion_time = obs_times[0]
    
    return {
        'semi_major_axis_au': float(a_au),
        'eccentricity': float(e),
        'inclination_deg': float(inc_deg),
        'raan_deg': float(raan_deg),
        'arg_periapsis_deg': float(argp_deg),
        'perihelion_time': perihelion_time,
        'comet_positions': comet_positions,
        'obs_times': obs_times
    }


def find_closest_approach_simple(orbit_data: dict, search_days: int = 730) -> Tuple[datetime, float, float]:
    """
    Find the closest approach of comet to Earth using simplified propagation.
    
    Args:
        orbit_data: Dictionary with orbital parameters
        search_days: Number of days to search forward
        
    Returns:
        Tuple of (datetime, distance_km, relative_speed_kms)
    """
    a_au = orbit_data['semi_major_axis_au']
    e = orbit_data['eccentricity']
    comet_positions = orbit_data['comet_positions']
    obs_times = orbit_data['obs_times']
    
    # Use first observation as reference
    epoch = obs_times[0]
    
    def distance_to_earth(days_offset):
        """Calculate distance from comet to Earth at given time offset."""
        t = Time(epoch + timedelta(days=days_offset))
        
        # Simple orbit propagation (circular approximation)
        # In reality, this should use proper Keplerian motion
        angle = 2 * np.pi * days_offset / (365.25 * a_au ** 1.5)  # Simplified Kepler's 3rd law
        
        # Approximate comet position
        r = a_au * AU_TO_KM * (1 - e * e) / (1 + e * np.cos(angle))
        comet_x = r * np.cos(angle)
        comet_y = r * np.sin(angle)
        comet_z = 0  # Simplified - assume ecliptic plane
        comet_pos = np.array([comet_x, comet_y, comet_z])
        
        # Get Earth position
        with solar_system_ephemeris.set('builtin'):
            earth_pos, _ = get_body_barycentric_posvel('earth', t)
            earth_pos_km = earth_pos.xyz.to(u.km).value
        
        # Calculate distance
        distance = np.linalg.norm(comet_pos - earth_pos_km)
        return distance
    
    # Find minimum distance
    result = minimize_scalar(
        distance_to_earth,
        bounds=(0, search_days),
        method='bounded'
    )
    
    closest_day = result.x
    min_distance_km = result.fun
    
    # Calculate datetime of closest approach
    closest_time = epoch + timedelta(days=closest_day)
    
    # Estimate relative velocity (simplified)
    # v = sqrt(mu * (2/r - 1/a))
    r_closest = min_distance_km
    v_comet = np.sqrt(SUN_MU * (2 / r_closest - 1 / (a_au * AU_TO_KM))) if r_closest > 0 else 30.0
    
    # Earth orbital velocity ~ 30 km/s
    v_earth = 30.0
    relative_velocity = abs(v_comet - v_earth)
    
    return closest_time, min_distance_km, relative_velocity


def compute_orbit_from_observations(observations: List[Observation]) -> ComputeResponse:
    """
    Main function to compute orbit and closest approach from observations.
    
    Args:
        observations: List of at least 5 observations
        
    Returns:
        ComputeResponse with orbit elements and closest approach data
    """
    if len(observations) < 5:
        raise ValueError("Need at least 5 observations")
    
    # Determine orbit using simplified method
    orbit_data = simple_orbit_determination(observations)
    
    # Extract orbital elements
    orbit_elements = OrbitElements(
        semi_major_axis_au=orbit_data['semi_major_axis_au'],
        eccentricity=orbit_data['eccentricity'],
        inclination_deg=orbit_data['inclination_deg'],
        raan_deg=orbit_data['raan_deg'],
        arg_periapsis_deg=orbit_data['arg_periapsis_deg'],
        perihelion_time=orbit_data['perihelion_time']
    )
    
    # Find closest approach to Earth
    closest_time, distance_km, speed_kms = find_closest_approach_simple(orbit_data)
    
    closest_approach = ClosestApproach(
        approach_datetime=closest_time,
        distance_km=float(distance_km),
        relative_speed_kms=float(speed_kms)
    )
    
    # Get IDs of observations used
    observation_ids = [obs.id for obs in observations]
    
    return ComputeResponse(
        orbit=orbit_elements,
        closest_approach=closest_approach,
        observation_ids=observation_ids
    )
