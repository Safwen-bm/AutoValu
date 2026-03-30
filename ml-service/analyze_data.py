import pandas as pd
import os

# File path
DATA_FILE = r"C:\Users\MSI\Desktop\deals-analyzer\ml-service\data\clean_data.csv"

# Load CSV
df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')

# 🔹 Clean basic columns
df['brand'] = df['brand'].str.strip().str.lower()
df['brand'] = df['brand'].replace({'mercedes-benz':'mercedes','citroën':'citroen'})

df['model'] = df['model'].str.strip().str.lower()
df['body_style'] = df['body_style'].str.strip().str.lower()

# ==============================
# DATA ANALYSIS
# ==============================
print("="*60)
print("DATA ANALYSIS")
print("="*60)

# 🔹 1. Brand distribution
print("\nTOP BRANDS:")
brand_counts = df['brand'].value_counts()
print(brand_counts.head(20))

# 🔹 2. Model distribution
print("\nTOP MODELS:")
model_counts = df['model'].value_counts()
print(model_counts.head(20))

# 🔹 3. Brand + Model + Body Style (MOST IMPORTANT)
print("\nBRAND + MODEL + BODY STYLE COUNTS:")
bmb_counts = df.groupby(['brand','model','body_style']).size().reset_index(name='count')
bmb_counts = bmb_counts.sort_values('count', ascending=False)
print(bmb_counts.head(50))

# 🔥 4. Weak data (models with <5 rows)
print("\nWEAK MODELS (need more data):")
weak = bmb_counts[bmb_counts['count'] < 5]
print(weak.head(50))

# 🔥 5. Strong models (models with >=20 rows)
print("\nSTRONG MODELS:")
strong = bmb_counts[bmb_counts['count'] >= 20]
print(strong.head(50))

# 🔹 Price stats per brand
print("\nBRAND PRICE STATS:")
print(df.groupby('brand')['price'].agg(['count','mean','median','min','max']).sort_values('count', ascending=False).head(20))

# 🔹 Model + Year counts
print("\nMODEL + YEAR COUNTS:")
my_counts = df.groupby(['model','year']).size().reset_index(name='count')
print(my_counts.sort_values('count', ascending=False).head(50))

# 🔥 6. Save to CSV
bmb_counts.to_csv("brand_model_body_counts.csv", index=False)
print("\nSaved: brand_model_body_counts.csv")

# 🔹 7. Optional: print brand + model + body for each car
print("\nFULL LIST: Brand | Model | Body Style for each car")
for idx, row in df.iterrows():
    print(f"{row['brand']} | {row['model']} | {row['body_style']}")