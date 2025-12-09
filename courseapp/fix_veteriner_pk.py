"""
Veteriner tablosundaki primary key sorununu düzeltir.
"""
import sqlite3
import os

# Veritabanı yolu
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Veteriner tablosundaki primary key düzeltiliyor...")

# 0. Eğer yeni tablo varsa sil
cursor.execute("DROP TABLE IF EXISTS veteriner_veteriner_new")

# 1. Yeni tablo oluştur (primary key ile)
cursor.execute("""
CREATE TABLE veteriner_veteriner_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT,
    telefon TEXT,
    email TEXT,
    il_id INTEGER,
    ilce_id INTEGER,
    mahalle_id INTEGER,
    mahalle_diger TEXT,
    adres_detay TEXT,
    kullanici_id INTEGER,
    aktif INTEGER DEFAULT 1,
    olusturulma NUMERIC,
    odeme_modeli TEXT DEFAULT 'PESIN',
    ilk_giris_sifre_degistirildi INTEGER DEFAULT 0,
    tahsis_sayisi INTEGER DEFAULT 0,
    satis_sayisi INTEGER DEFAULT 0,
    uzmanlik_alanlari TEXT,
    calisma_saatleri TEXT,
    acil_hizmet INTEGER DEFAULT 0,
    evde_hizmet INTEGER DEFAULT 0,
    hizmet_verilen_ilceler TEXT,
    website TEXT,
    instagram TEXT,
    facebook TEXT,
    twitter TEXT,
    linkedin TEXT,
    youtube TEXT,
    tema TEXT,
    birincil_renk TEXT,
    logo TEXT,
    cta_metin TEXT,
    cta_link TEXT,
    whatsapp TEXT,
    goster_sosyal INTEGER DEFAULT 1,
    goster_hizmetler INTEGER DEFAULT 1,
    goster_calisma_saatleri INTEGER DEFAULT 1,
    goster_galeri INTEGER DEFAULT 1,
    pazartesi_baslangic NUMERIC,
    pazartesi_bitis NUMERIC,
    pazartesi_kapali INTEGER DEFAULT 0,
    sali_baslangic NUMERIC,
    sali_bitis NUMERIC,
    sali_kapali INTEGER DEFAULT 0,
    carsamba_baslangic NUMERIC,
    carsamba_bitis NUMERIC,
    carsamba_kapali INTEGER DEFAULT 0,
    persembe_baslangic NUMERIC,
    persembe_bitis NUMERIC,
    persembe_kapali INTEGER DEFAULT 0,
    cuma_baslangic NUMERIC,
    cuma_bitis NUMERIC,
    cuma_kapali INTEGER DEFAULT 0,
    cumartesi_baslangic NUMERIC,
    cumartesi_bitis NUMERIC,
    cumartesi_kapali INTEGER DEFAULT 0,
    pazar_baslangic NUMERIC,
    pazar_bitis NUMERIC,
    pazar_kapali INTEGER DEFAULT 1,
    ortalama_puan NUMERIC DEFAULT 0.0,
    degerlendirme_sayisi INTEGER DEFAULT 0,
    web_baslik TEXT,
    web_slogan TEXT,
    web_aciklama TEXT,
    hizmet1_baslik TEXT,
    hizmet1_aciklama TEXT,
    hizmet1_icon TEXT,
    hizmet2_baslik TEXT,
    hizmet2_aciklama TEXT,
    hizmet2_icon TEXT,
    hizmet3_baslik TEXT,
    hizmet3_aciklama TEXT,
    hizmet3_icon TEXT,
    web_resim1 TEXT,
    web_resim2 TEXT,
    web_resim3 TEXT,
    web_seo_baslik TEXT,
    web_seo_aciklama TEXT,
    web_seo_anahtar_kelimeler TEXT,
    web_slug TEXT UNIQUE,
    web_aktif INTEGER DEFAULT 0,
    konum_koordinat TEXT,
    hizmet4_aciklama TEXT,
    hizmet4_baslik TEXT,
    hizmet4_icon TEXT,
    hizmet5_aciklama TEXT,
    hizmet5_baslik TEXT,
    hizmet5_icon TEXT,
    hizmet6_aciklama TEXT,
    hizmet6_baslik TEXT,
    hizmet6_icon TEXT,
    hizmet7_aciklama TEXT,
    hizmet7_baslik TEXT,
    hizmet7_icon TEXT,
    hizmet8_aciklama TEXT,
    hizmet8_baslik TEXT,
    hizmet8_icon TEXT,
    hizmet9_aciklama TEXT,
    hizmet9_baslik TEXT,
    hizmet9_icon TEXT,
    FOREIGN KEY (il_id) REFERENCES anahtarlik_il(id),
    FOREIGN KEY (ilce_id) REFERENCES anahtarlik_ilce(id),
    FOREIGN KEY (mahalle_id) REFERENCES anahtarlik_mahalle(id),
    FOREIGN KEY (kullanici_id) REFERENCES auth_user(id)
)
""")

# 2. Eski tablodan verileri kopyala (id hariç, otomatik oluşacak)
print("Veriler kopyalanıyor...")
cursor.execute("""
INSERT INTO veteriner_veteriner_new (
    ad, telefon, email, il_id, ilce_id, mahalle_id, mahalle_diger, adres_detay,
    kullanici_id, aktif, olusturulma, odeme_modeli, ilk_giris_sifre_degistirildi,
    tahsis_sayisi, satis_sayisi, uzmanlik_alanlari, calisma_saatleri,
    acil_hizmet, evde_hizmet, hizmet_verilen_ilceler, website, instagram,
    facebook, twitter, linkedin, youtube, tema, birincil_renk, logo,
    cta_metin, cta_link, whatsapp, goster_sosyal, goster_hizmetler,
    goster_calisma_saatleri, goster_galeri, pazartesi_baslangic, pazartesi_bitis,
    pazartesi_kapali, sali_baslangic, sali_bitis, sali_kapali,
    carsamba_baslangic, carsamba_bitis, carsamba_kapali, persembe_baslangic,
    persembe_bitis, persembe_kapali, cuma_baslangic, cuma_bitis, cuma_kapali,
    cumartesi_baslangic, cumartesi_bitis, cumartesi_kapali, pazar_baslangic,
    pazar_bitis, pazar_kapali, ortalama_puan, degerlendirme_sayisi,
    web_baslik, web_slogan, web_aciklama, hizmet1_baslik, hizmet1_aciklama,
    hizmet1_icon, hizmet2_baslik, hizmet2_aciklama, hizmet2_icon,
    hizmet3_baslik, hizmet3_aciklama, hizmet3_icon, web_resim1, web_resim2,
    web_resim3, web_seo_baslik, web_seo_aciklama, web_seo_anahtar_kelimeler,
    web_slug, web_aktif, konum_koordinat, hizmet4_aciklama, hizmet4_baslik,
    hizmet4_icon, hizmet5_aciklama, hizmet5_baslik, hizmet5_icon,
    hizmet6_aciklama, hizmet6_baslik, hizmet6_icon, hizmet7_aciklama,
    hizmet7_baslik, hizmet7_icon, hizmet8_aciklama, hizmet8_baslik,
    hizmet8_icon, hizmet9_aciklama, hizmet9_baslik, hizmet9_icon
)
SELECT 
    ad, telefon, email, il_id, ilce_id, mahalle_id, mahalle_diger, adres_detay,
    kullanici_id, aktif, olusturulma, odeme_modeli, ilk_giris_sifre_degistirildi,
    tahsis_sayisi, satis_sayisi, uzmanlik_alanlari, calisma_saatleri,
    acil_hizmet, evde_hizmet, hizmet_verilen_ilceler, website, instagram,
    facebook, twitter, linkedin, youtube, tema, birincil_renk, logo,
    cta_metin, cta_link, whatsapp, goster_sosyal, goster_hizmetler,
    goster_calisma_saatleri, goster_galeri, pazartesi_baslangic, pazartesi_bitis,
    pazartesi_kapali, sali_baslangic, sali_bitis, sali_kapali,
    carsamba_baslangic, carsamba_bitis, carsamba_kapali, persembe_baslangic,
    persembe_bitis, persembe_kapali, cuma_baslangic, cuma_bitis, cuma_kapali,
    cumartesi_baslangic, cumartesi_bitis, cumartesi_kapali, pazar_baslangic,
    pazar_bitis, pazar_kapali, ortalama_puan, degerlendirme_sayisi,
    web_baslik, web_slogan, web_aciklama, hizmet1_baslik, hizmet1_aciklama,
    hizmet1_icon, hizmet2_baslik, hizmet2_aciklama, hizmet2_icon,
    hizmet3_baslik, hizmet3_aciklama, hizmet3_icon, web_resim1, web_resim2,
    web_resim3, web_seo_baslik, web_seo_aciklama, web_seo_anahtar_kelimeler,
    web_slug, web_aktif, konum_koordinat, hizmet4_aciklama, hizmet4_baslik,
    hizmet4_icon, hizmet5_aciklama, hizmet5_baslik, hizmet5_icon,
    hizmet6_aciklama, hizmet6_baslik, hizmet6_icon, hizmet7_aciklama,
    hizmet7_baslik, hizmet7_icon, hizmet8_aciklama, hizmet8_baslik,
    hizmet8_icon, hizmet9_aciklama, hizmet9_baslik, hizmet9_icon
FROM veteriner_veteriner
""")

# 3. Eski tabloyu sil
print("Eski tablo siliniyor...")
cursor.execute("DROP TABLE veteriner_veteriner")

# 4. Yeni tabloyu eski isimle yeniden adlandır
print("Yeni tablo adlandırılıyor...")
cursor.execute("ALTER TABLE veteriner_veteriner_new RENAME TO veteriner_veteriner")

# 5. Index'leri yeniden oluştur
print("Index'ler oluşturuluyor...")
cursor.execute("CREATE INDEX IF NOT EXISTS veteriner_veteriner_il_id_idx ON veteriner_veteriner(il_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS veteriner_veteriner_ilce_id_idx ON veteriner_veteriner(ilce_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS veteriner_veteriner_kullanici_id_idx ON veteriner_veteriner(kullanici_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS veteriner_veteriner_web_slug_idx ON veteriner_veteriner(web_slug)")

conn.commit()
print("✓ Primary key düzeltildi!")

# Kontrol et
cursor.execute("PRAGMA table_info(veteriner_veteriner)")
cols = cursor.fetchall()
pk_col = [col for col in cols if col[5] == 1]
if pk_col:
    print(f"✓ Primary key: {pk_col[0][1]}")
else:
    print("✗ Primary key bulunamadı!")

cursor.execute("SELECT COUNT(*) FROM veteriner_veteriner")
count = cursor.fetchone()[0]
print(f"✓ Toplam {count} veteriner kaydı korundu.")

conn.close()

