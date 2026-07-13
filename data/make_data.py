"""Generate a realistic e-commerce transactions dataset for a Pakistan-based
online retailer, with the messiness real transactional data always has."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(2024)

# ---------------------------------------------------------------- catalogue
products = [
    # (name, category, unit_cost, unit_price)
    ("Cotton Kurta",          "Apparel",     1200,  2499),
    ("Embroidered Shawl",     "Apparel",     1800,  3999),
    ("Lawn Suit (3pc)",       "Apparel",     2200,  4499),
    ("Leather Sandals",       "Footwear",    1500,  3299),
    ("Khussa Shoes",          "Footwear",     900,  1999),
    ("Wireless Earbuds",      "Electronics", 2800,  5999),
    ("Power Bank 20000mAh",   "Electronics", 1900,  3799),
    ("Bluetooth Speaker",     "Electronics", 2400,  4999),
    ("Ceramic Dinner Set",    "Home",        3200,  6499),
    ("Cushion Covers (4pc)",  "Home",         700,  1599),
    ("Table Lamp",            "Home",        1100,  2299),
    ("Skincare Bundle",       "Beauty",      1400,  2999),
    ("Attar Perfume",         "Beauty",       800,  1899),
    ("Makeup Kit",            "Beauty",      2100,  4299),
]
prod_df = pd.DataFrame(products, columns=["product", "category", "unit_cost", "unit_price"])

cities = ["Lahore", "Karachi", "Islamabad", "Faisalabad", "Rawalpindi", "Multan", "Peshawar"]
city_w = [0.28, 0.30, 0.14, 0.09, 0.08, 0.06, 0.05]

channels = ["Website", "Mobile App", "Social Media"]
channel_w = [0.40, 0.45, 0.15]

segments = ["New", "Returning", "Loyal"]

# ---------------------------------------------------------------- customers
n_customers = 1800
customers = pd.DataFrame({
    "customer_id": [f"C{str(i).zfill(5)}" for i in range(1, n_customers + 1)],
    "city": rng.choice(cities, n_customers, p=city_w),
    "signup_month": rng.integers(1, 25, n_customers),  # months since start
})

# ---------------------------------------------------------------- orders
dates = pd.date_range("2023-01-01", "2024-12-31", freq="D")
rows = []
order_no = 100000

for d in dates:
    doy = d.dayofyear
    month = d.month

    # Baseline daily orders, growing over time
    base = 22 + 0.025 * (d - dates[0]).days

    # Seasonality: Eid spikes, winter wedding season, summer lull
    seasonal = 1.0
    if month in (3, 4):        seasonal = 1.45   # Ramadan / Eid al-Fitr
    elif month in (6,):        seasonal = 1.30   # Eid al-Adha
    elif month in (11, 12):    seasonal = 1.35   # wedding + winter
    elif month in (7, 8):      seasonal = 0.80   # monsoon lull

    # Weekend uplift
    if d.dayofweek in (5, 6):
        seasonal *= 1.15

    n_orders = max(1, int(rng.poisson(base * seasonal)))

    for _ in range(n_orders):
        order_no += 1
        cust = customers.iloc[rng.integers(0, n_customers)]

        # Basket: 1-4 line items
        n_items = rng.choice([1, 2, 3, 4], p=[0.52, 0.28, 0.14, 0.06])
        picks = rng.choice(len(prod_df), size=n_items, replace=False)

        channel = rng.choice(channels, p=channel_w)

        # Discounts more common in sale months
        disc = 0.0
        if rng.random() < (0.35 if month in (3, 4, 11) else 0.15):
            disc = rng.choice([0.05, 0.10, 0.15, 0.20])

        # ~7% of orders get returned
        returned = rng.random() < 0.07

        for pi in picks:
            p = prod_df.iloc[pi]
            qty = int(rng.choice([1, 1, 1, 2, 2, 3], p=[.4, .2, .15, .12, .08, .05]))
            rows.append({
                "order_id": f"ORD{order_no}",
                "order_date": d.strftime("%Y-%m-%d"),
                "customer_id": cust["customer_id"],
                "city": cust["city"],
                "channel": channel,
                "product": p["product"],
                "category": p["category"],
                "quantity": qty,
                "unit_price": p["unit_price"],
                "unit_cost": p["unit_cost"],
                "discount_pct": disc,
                "returned": returned,
            })

df = pd.DataFrame(rows)

# ---------------------------------------------------------------- messiness
# 1. inconsistent city capitalisation / whitespace
idx = rng.choice(df.index, 400, replace=False)
df.loc[idx, "city"] = df.loc[idx, "city"].str.upper()
idx = rng.choice(df.index, 300, replace=False)
df.loc[idx, "city"] = " " + df.loc[idx, "city"].astype(str)

# 2. missing channel on some rows
idx = rng.choice(df.index, int(len(df) * 0.02), replace=False)
df.loc[idx, "channel"] = np.nan

# 3. duplicate rows (double-logged line items)
dupes = df.sample(150, random_state=5)
df = pd.concat([df, dupes], ignore_index=True)

# 4. a few impossible quantities (data entry errors)
idx = rng.choice(df.index, 25, replace=False)
df.loc[idx, "quantity"] = 0

df = df.sample(frac=1, random_state=11).reset_index(drop=True)
df.to_csv("/home/claude/dash/data/ecommerce_orders_raw.csv", index=False)

print(f"rows: {len(df):,}")
print(f"orders: {df.order_id.nunique():,}  customers: {df.customer_id.nunique():,}")
print(df.head(3).to_string())
