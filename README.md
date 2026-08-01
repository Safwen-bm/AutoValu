# AutoValu

**AI-powered used car price checker for the Tunisian market.**

AutoValu tells buyers and sellers whether a used car price is a great deal, fair, or overpriced — instantly, based on real market data instead of gut feeling.

---

## 🚀 What it does

- Enter a car's brand, model, year, mileage, fuel, condition, etc.
- Get a predicted fair market price with a confidence range
- If checking a listing price, get an instant verdict (excellent deal / fair / expensive / overpriced) with a suggested counter-offer
- Buyer mode (check a price you saw) and Seller mode (get a recommended asking price)
- Admin dashboard to review user-submitted prices and monitor usage stats

---

## 🧠 The ML system

The core problem: a single model averages prices across wildly different vehicles, which poisons predictions (a Hilux and a Yaris from the same brand don't depreciate the same way).

- **Two segment-specific XGBoost models** (budget vs. mid/premium), routed dynamically based on a reference price
- **Model-zone target encoding**: prices are encoded per model *and* depreciation age zone (e.g. `hilux_z2`), not just per brand, so rare/expensive models aren't dragged toward the brand average
- **KNN nearest-neighbor search** finds the closest real comparable listings (same model, year, mileage, fuel, condition) and blends its estimate with the XGBoost prediction, weighted by how close the match is
- Trained on 3,300+ real Tunisian listings scraped and cleaned from local marketplaces
- ~84% average prediction accuracy (MAPE-based)

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React, TypeScript |
| Backend | NestJS (API gateway between frontend and ML service) |
| ML Service | FastAPI, XGBoost, scikit-learn, pandas |
| Database | PostgreSQL |
| Deployment | Vercel (frontend), Render (backend + ML service) |

---

## 🏗️ Architecture

```
deals-analyzer/
├── frontend/      # Next.js — landing page, price checker, admin dashboard
├── backend/       # NestJS — API gateway, request validation
└── ml-service/    # FastAPI — model inference, KNN, training scripts
```

The NestJS backend doesn't run any ML itself — it validates and forwards requests to the FastAPI service, which handles prediction, KNN matching, and persistence to PostgreSQL. This keeps the ML logic (Python) and the API layer (TypeScript) cleanly separated.

---

## 📊 Admin Dashboard

- Review and approve/reject user-submitted real prices (used to grow the training dataset)
- Live stats: total queries, top searched brands, submission approval rates
- Full query log for auditing model behavior

---

## 📄 License

**All rights reserved.**

This project and its source code are proprietary. No part of this repository may be copied, modified, distributed, or used in any form without explicit written permission from the author.

© Safwen Ben Mabrouk

---

## 📬 Contact

**Safwen Ben Mabrouk** — Full-Stack Software Engineer
- Email: safwenbenmabrouk@gmail.com
- LinkedIn: [linkedin.com/in/safwen-ben-mabrouk](https://linkedin.com/in/safwen-ben-mabrouk)
- GitHub: [@Safwen-bm](https://github.com/Safwen-bm)