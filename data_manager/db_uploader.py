"""
데이터 업로더: CSV 파일을 Supabase에 업로드
"""
import os
import csv
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    """Supabase 클라이언트 초기화"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL 및 SUPABASE_KEY/SUPABASE_SERVICE_ROLE_KEY 환경변수가 필요합니다")

    return create_client(url, key)

def upload_products_from_csv(csv_path: str):
    """
    products_rows.csv 파일을 읽어서 Supabase products 테이블에 업로드
    """
    supabase = get_supabase_client()

    print(f"📂 CSV 파일 읽는 중: {csv_path}")

    products = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            product = {
                'source': row['source'] or None,
                'source_product_id': row['source_product_id'] or None,
                'url': row['url'] or None,
                'title': row['title'] or None,
                'brand': row['brand'] or None,
                'category': row['category'] or None,
                'price': int(row['price']) if row['price'] and row['price'].strip() else None,
                'currency': row['currency'] or None,
                'rating_avg': float(row['rating_avg']) if row['rating_avg'] and row['rating_avg'].strip() else None,
                'rating_count': int(row['rating_count']) if row['rating_count'] and row['rating_count'].strip() else None,
            }
            products.append(product)

    print(f"📦 {len(products)}개의 제품 발견")

    if not products:
        print("⚠️ 업로드할 제품이 없습니다")
        return

    print(f"⬆️ Supabase에 업로드 중...")

    try:
        response = supabase.table('products').upsert(
            products,
            on_conflict='source,source_product_id'
        ).execute()

        print(f"✅ {len(products)}개의 제품이 성공적으로 업로드되었습니다!")
        print(f"📊 업로드된 제품:")
        for p in products:
            print(f"  - {p['brand']}: {p['title'][:50]}...")

    except Exception as e:
        print(f"❌ 업로드 중 오류 발생: {e}")
        raise

def upload_reviews_from_csv(csv_path: str):
    """
    reviews_rows.csv 파일을 읽어서 Supabase reviews 테이블에 업로드
    """
    supabase = get_supabase_client()

    print(f"📂 CSV 파일 읽는 중: {csv_path}")

    reviews = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            review = {
                'product_id': int(row['product_id']) if row['product_id'] and row['product_id'].strip() else None,
                'source': row['source'] or None,
                'source_review_id': row['source_review_id'] or None,
                'author': row['author'] or None,
                'rating': int(row['rating']) if row['rating'] and row['rating'].strip() else None,
                'title': row['title'] or None,
                'body': row['body'] or None,
                'language': row['language'] or None,
                'helpful_count': int(row['helpful_count']) if row['helpful_count'] and row['helpful_count'].strip() else None,
                'review_date': row['review_date'] or None,
            }
            reviews.append(review)

    print(f"📝 {len(reviews)}개의 리뷰 발견")

    if not reviews:
        print("⚠️ 업로드할 리뷰가 없습니다")
        return

    print(f"⬆️ Supabase에 업로드 중...")

    try:
        response = supabase.table('reviews').upsert(
            reviews,
            on_conflict='source,source_review_id'
        ).execute()

        print(f"✅ {len(reviews)}개의 리뷰가 성공적으로 업로드되었습니다!")

    except Exception as e:
        print(f"❌ 업로드 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python db_uploader.py [products|reviews|all]")
        print("  products: products_rows.csv 업로드")
        print("  reviews: reviews_rows.csv 업로드")
        print("  all: 두 파일 모두 업로드")
        sys.exit(1)

    mode = sys.argv[1]
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if mode in ['products', 'all']:
        products_csv = os.path.join(base_dir, 'products_rows.csv')
        if os.path.exists(products_csv):
            upload_products_from_csv(products_csv)
        else:
            print(f"❌ 파일을 찾을 수 없습니다: {products_csv}")

    if mode in ['reviews', 'all']:
        reviews_csv = os.path.join(base_dir, 'reviews_rows.csv')
        if os.path.exists(reviews_csv):
            upload_reviews_from_csv(reviews_csv)
        else:
            print(f"❌ 파일을 찾을 수 없습니다: {reviews_csv}")
