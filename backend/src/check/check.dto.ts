// backend/src/check/check.dto.ts

export class CheckCarDto {
  brand: string;
  model?: string;
  year: number;
  fuel?: string;
  body_style?: string;
  car_condition?: string;
  trim_level?: string;
  mileage_km?: number;
  engine_cc?: number;
  seats?: number;
  doors?: number;
  user_price?: number;  // buyer mode: price they saw
}