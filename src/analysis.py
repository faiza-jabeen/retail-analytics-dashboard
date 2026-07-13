"""
E-Commerce Business Analytics
=============================
Cleans raw transaction data and computes the KPIs a business actually
runs on: revenue, margin, AOV, customer retention, and channel performance.

Author: Faiza Jabeen
"""

import numpy as np
import pandas as pd
import json

RAW = "data/ecommerce_orders_raw.csv"
CLEAN = "data/ecommerce_orders_clean.csv"


# ---------------------------------------------------------------- clean
def clean_data() -> pd.DataFrame:
    df = pd.read_csv(RAW)
    print(f"Raw: {len(df):,} rows")

    # City names arrive with inconsistent casing and stray whitespace.
    # Left unfixed, 'LAHORE' and 'Lahore' would report as two separate cities.
    df["city"] = df["city"].str.strip().str.title()

    # Duplicate line items are double-logging artefacts, not real sales.
    before = len(df)
    df = df.drop_duplicates()
    print(f"Dropped {before - len(df):,} duplicate rows")

    # Quantity of zero is a data-entry error: an order line that sold nothing
    # is not a sale, and leaving it in would understate average order value.
    before = len(df)
    df = df[df["quantity"] > 0]
    print(f"Dropped {before - len(df):,} rows with zero quantity")

    # Missing channel: kept, but labelled honestly rather than guessed at.
    df["channel"] = df["channel"].fillna("Unknown")

    df["order_date"] = pd.to_datetime(df["order_date"])

    # ---- derived financial columns ----
    df["gross_revenue"] = df["quantity"] * df["unit_price"]
    df["discount_value"] = df["gross_revenue"] * df["discount_pct"]
    df["net_revenue"] = df["gross_revenue"] - df["discount_value"]
    df["cogs"] = df["quantity"] * df["unit_cost"]
    df["gross_profit"] = df["net_revenue"] - df["cogs"]

    # Returned orders earn no revenue but the cost is still incurred.
    df["realised_revenue"] = np.where(df["returned"], 0, df["net_revenue"])
    df["realised_profit"] = np.where(df["returned"], -df["cogs"], df["gross_profit"])

    df["year_month"] = df["order_date"].dt.to_period("M").astype(str)

    df.to_csv(CLEAN, index=False)
    print(f"Clean: {len(df):,} rows\n")
    return df


# ---------------------------------------------------------------- KPIs
def headline_kpis(df: pd.DataFrame) -> dict:
    orders = df.groupby("order_id").agg(
        revenue=("realised_revenue", "sum"),
        profit=("realised_profit", "sum"),
        returned=("returned", "first"),
    )

    total_rev = orders["revenue"].sum()
    total_profit = orders["profit"].sum()
    n_orders = len(orders)
    n_customers = df["customer_id"].nunique()

    kpis = {
        "total_revenue": float(total_rev),
        "gross_profit": float(total_profit),
        "margin_pct": float(total_profit / total_rev * 100),
        "total_orders": int(n_orders),
        "unique_customers": int(n_customers),
        "avg_order_value": float(total_rev / n_orders),
        "orders_per_customer": float(n_orders / n_customers),
        "return_rate_pct": float(orders["returned"].mean() * 100),
        "revenue_lost_to_returns": float(
            df.loc[df["returned"], "net_revenue"].sum()
        ),
        "revenue_lost_to_discounts": float(df["discount_value"].sum()),
    }

    print("HEADLINE KPIs")
    print("-" * 52)
    print(f"Total revenue         PKR {kpis['total_revenue']:>15,.0f}")
    print(f"Gross profit          PKR {kpis['gross_profit']:>15,.0f}")
    print(f"Gross margin              {kpis['margin_pct']:>14.1f}%")
    print(f"Orders                    {kpis['total_orders']:>15,}")
    print(f"Customers                 {kpis['unique_customers']:>15,}")
    print(f"Avg order value       PKR {kpis['avg_order_value']:>15,.0f}")
    print(f"Return rate               {kpis['return_rate_pct']:>14.1f}%")
    print(f"Lost to returns       PKR {kpis['revenue_lost_to_returns']:>15,.0f}")
    print(f"Lost to discounts     PKR {kpis['revenue_lost_to_discounts']:>15,.0f}")
    print()
    return kpis


# ---------------------------------------------------------------- breakdowns
def build_breakdowns(df: pd.DataFrame) -> dict:
    out = {}

    # Monthly trend
    monthly = (df.groupby("year_month")
                 .agg(revenue=("realised_revenue", "sum"),
                      profit=("realised_profit", "sum"),
                      orders=("order_id", "nunique"))
                 .reset_index())
    monthly["aov"] = monthly["revenue"] / monthly["orders"]
    out["monthly"] = monthly.to_dict("records")

    # Category performance — revenue AND margin, because high revenue
    # at low margin is not the same as a healthy category.
    cat = (df.groupby("category")
             .agg(revenue=("realised_revenue", "sum"),
                  profit=("realised_profit", "sum"),
                  units=("quantity", "sum"))
             .reset_index())
    cat["margin_pct"] = cat["profit"] / cat["revenue"] * 100
    cat = cat.sort_values("revenue", ascending=False)
    out["category"] = cat.to_dict("records")

    # City
    city = (df.groupby("city")
              .agg(revenue=("realised_revenue", "sum"),
                   orders=("order_id", "nunique"),
                   customers=("customer_id", "nunique"))
              .reset_index()
              .sort_values("revenue", ascending=False))
    out["city"] = city.to_dict("records")

    # Channel
    chan = (df.groupby("channel")
              .agg(revenue=("realised_revenue", "sum"),
                   orders=("order_id", "nunique"))
              .reset_index())
    chan["aov"] = chan["revenue"] / chan["orders"]
    chan = chan.sort_values("revenue", ascending=False)
    out["channel"] = chan.to_dict("records")

    # Top products
    prod = (df.groupby(["product", "category"])
              .agg(revenue=("realised_revenue", "sum"),
                   profit=("realised_profit", "sum"),
                   units=("quantity", "sum"))
              .reset_index()
              .sort_values("revenue", ascending=False)
              .head(10))
    out["top_products"] = prod.to_dict("records")

    print("TOP CATEGORIES BY REVENUE")
    print("-" * 52)
    for r in out["category"]:
        print(f"{r['category']:<14} PKR {r['revenue']:>13,.0f}   "
              f"margin {r['margin_pct']:>5.1f}%")
    print()

    return out


# ---------------------------------------------------------------- retention
def cohort_retention(df: pd.DataFrame) -> dict:
    """Group customers by the month of their first order, then track what
    share of each cohort came back in later months.

    This is the metric that separates a growing business from one that is
    simply buying new customers to replace the ones it loses."""

    orders = (df.groupby(["customer_id", "order_id"])
                .agg(order_date=("order_date", "first"))
                .reset_index())

    first = orders.groupby("customer_id")["order_date"].min().rename("cohort_date")
    orders = orders.join(first, on="customer_id")

    orders["cohort"] = orders["cohort_date"].dt.to_period("M")
    orders["period"] = orders["order_date"].dt.to_period("M")
    orders["months_since"] = (orders["period"] - orders["cohort"]).apply(lambda x: x.n)

    pivot = (orders.groupby(["cohort", "months_since"])["customer_id"]
                   .nunique()
                   .unstack(fill_value=0))

    size = pivot[0]
    retention = pivot.divide(size, axis=0) * 100

    # Keep first 12 months, and only cohorts with enough customers to be
    # meaningful — a 2-person cohort with 50% retention tells you nothing.
    retention = retention.iloc[:, :12]
    retention = retention[size >= 20]

    result = {
        "cohorts": [str(c) for c in retention.index],
        "cohort_sizes": size[size >= 20].tolist(),
        "matrix": retention.round(1).values.tolist(),
    }

    m1 = retention[1].mean() if 1 in retention.columns else 0
    m3 = retention[3].mean() if 3 in retention.columns else 0
    m6 = retention[6].mean() if 6 in retention.columns else 0

    result["avg_month1"] = round(float(m1), 1)
    result["avg_month3"] = round(float(m3), 1)
    result["avg_month6"] = round(float(m6), 1)

    print("COHORT RETENTION")
    print("-" * 52)
    print(f"Month 1 return rate   {m1:>5.1f}%")
    print(f"Month 3 return rate   {m3:>5.1f}%")
    print(f"Month 6 return rate   {m6:>5.1f}%")
    print()

    return result


# ---------------------------------------------------------------- RFM
def rfm_segments(df: pd.DataFrame) -> dict:
    """Segment customers by Recency, Frequency and Monetary value.

    A blunt but genuinely useful model: it tells the business who to
    keep, who to win back, and who not to waste marketing budget on."""

    snapshot = df["order_date"].max() + pd.Timedelta(days=1)

    rfm = (df.groupby("customer_id")
             .agg(recency=("order_date", lambda s: (snapshot - s.max()).days),
                  frequency=("order_id", "nunique"),
                  monetary=("realised_revenue", "sum")))

    # Score each dimension 1-4. Recency is reversed: recent is better.
    rfm["r_score"] = pd.qcut(rfm["recency"], 4, labels=[4, 3, 2, 1]).astype(int)
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"),
                             4, labels=[1, 2, 3, 4]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"], 4, labels=[1, 2, 3, 4]).astype(int)

    def label(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 3 and f >= 3 and m >= 3:  return "Champions"
        if r >= 3 and f >= 2:             return "Loyal"
        if r >= 3 and f == 1:             return "New / Promising"
        if r == 2 and f >= 2:             return "At Risk"
        if r == 1 and f >= 3:             return "Cannot Lose"
        return "Hibernating"

    rfm["segment"] = rfm.apply(label, axis=1)

    seg = (rfm.groupby("segment")
              .agg(customers=("recency", "size"),
                   revenue=("monetary", "sum"),
                   avg_orders=("frequency", "mean"))
              .reset_index()
              .sort_values("revenue", ascending=False))
    seg["revenue_share_pct"] = seg["revenue"] / seg["revenue"].sum() * 100
    seg["customer_share_pct"] = seg["customers"] / seg["customers"].sum() * 100

    print("CUSTOMER SEGMENTS (RFM)")
    print("-" * 52)
    for _, r in seg.iterrows():
        print(f"{r['segment']:<18} {r['customers']:>5} customers "
              f"({r['customer_share_pct']:>4.1f}%)  "
              f"{r['revenue_share_pct']:>5.1f}% of revenue")
    print()

    return {"segments": seg.to_dict("records")}


# ---------------------------------------------------------------- main
def main():
    print("=" * 52)
    print("E-COMMERCE BUSINESS ANALYTICS")
    print("=" * 52 + "\n")

    df = clean_data()
    kpis = headline_kpis(df)
    breakdowns = build_breakdowns(df)
    retention = cohort_retention(df)
    rfm = rfm_segments(df)

    payload = {
        "kpis": kpis,
        **breakdowns,
        "retention": retention,
        **rfm,
    }

    with open("outputs/dashboard_data.json", "w") as f:
        json.dump(payload, f, indent=2, default=str)

    print("Written to outputs/dashboard_data.json")


if __name__ == "__main__":
    main()
