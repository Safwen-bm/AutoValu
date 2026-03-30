// backend/src/main.ts
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Allow frontend (Next.js on port 3000) to call this backend
  app.enableCors({
    origin: ['http://localhost:3000', 'https://*.vercel.app'],
    methods: ['GET', 'POST'],
  });

  await app.listen(4000);
  console.log('Backend running on http://localhost:4000');
}
bootstrap();