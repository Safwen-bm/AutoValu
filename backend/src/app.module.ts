// backend/src/app.module.ts
import { Module } from '@nestjs/common';
import { CheckModule } from './check/check.module';

@Module({
  imports: [CheckModule],
})
export class AppModule {}