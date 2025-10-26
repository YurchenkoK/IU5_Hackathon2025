export interface Observation {
  id: number;
  ra_hours: number;
  dec_degrees: number;
  observation_time: string;
  photo_url: string;
}

export interface OrbitElements {
  semi_major_axis_au: number;
  eccentricity: number;
  inclination_deg: number;
  raan_deg: number;
  arg_periapsis_deg: number;
  perihelion_time: string;
}

export interface ClosestApproach {
  approach_datetime: string;
  distance_km: number;
  relative_speed_kms: number;
}

export interface ComputeResponse {
  orbit: OrbitElements;
  closest_approach: ClosestApproach;
  observation_ids: number[];
}
