// check.service.ts
import { Injectable, HttpException, HttpStatus } from '@nestjs/common';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

@Injectable()
export class CheckService {

  async checkPrice(dto: any): Promise<any> {
    try {
      const res = await fetch(`${PYTHON_API_URL}/predict`, {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify(dto),
      });
      if (!res.ok) throw new HttpException(`ML error: ${await res.text()}`, HttpStatus.BAD_GATEWAY);
      return res.json();
    } catch (e) {
      if (e instanceof HttpException) throw e;
      throw new HttpException('ML service offline', HttpStatus.SERVICE_UNAVAILABLE);
    }
  }

  async submitPrice(dto: any): Promise<any> {
    try {
      const res = await fetch(`${PYTHON_API_URL}/submit`, {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify(dto),
      });
      if (!res.ok) throw new HttpException(`Submit error: ${await res.text()}`, HttpStatus.BAD_GATEWAY);
      return res.json();
    } catch (e) {
      if (e instanceof HttpException) throw e;
      throw new HttpException('ML service offline', HttpStatus.SERVICE_UNAVAILABLE);
    }
  }

  async healthCheck(): Promise<any> {
    try {
      const res  = await fetch(`${PYTHON_API_URL}/health`);
      const data = await res.json();
      return { backend: 'ok', ml_service: data };
    } catch {
      return { backend: 'ok', ml_service: 'offline' };
    }
  }
}