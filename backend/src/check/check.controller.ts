// check.controller.ts
import { Controller, Post, Get, Body, Query } from '@nestjs/common';
import { CheckService } from './check.service';

@Controller('api')
export class CheckController {
  constructor(private readonly checkService: CheckService) {}

  @Post('check')
  checkPrice(@Body() dto: any) {
    return this.checkService.checkPrice(dto);
  }

  @Post('submit')
  submitPrice(@Body() dto: any) {
    return this.checkService.submitPrice(dto);
  }

  @Get('health')
  health() {
    return this.checkService.healthCheck();
  }
}