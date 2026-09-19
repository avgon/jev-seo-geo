# jev-seo-geo Kullanım Kılavuzu

`jev-seo-geo`, bir sitenin veya içeriğin AI aramalarındaki görünürlüğünü ölçmek ve iyileştirmek için tasarlanmış açık kaynak araç kitidir.

- **SEO:** Google gibi klasik arama motorlarındaki görünürlük.
- **GEO:** ChatGPT, Claude, Gemini ve Perplexity gibi üretken AI yanıtlarında görünürlük.

Araç iki parçadan oluşur:

1. **Jev karar motoru:** İçerik kalitesi, başlık seçimi ve eksiklerin hızlı analizi.
2. **İsteğe bağlı LLM probe/yeniden-yazım:** Bir markanın AI yanıtlarında geçip geçmediğini ölçme ve içeriği önerilere göre iyileştirme.

## 1. Kurulum

```bash
pip install jev-seo-geo
```

Kaynak koddan denemek için:

```bash
git clone https://github.com/avgon/jev-seo-geo.git
cd jev-seo-geo
pip install -e .
```

## 2. Anahtarlar

Her özellik için sadece `TYPESAFE_API_KEY` gerekir:

```bash
export TYPESAFE_API_KEY="apikey_..."
```

Marka probe ve otomatik rewrite için en az bir üretken model anahtarı ekleyin:

```bash
export OPENAI_API_KEY="sk-..."
# veya
export ANTHROPIC_API_KEY="sk-ant-..."
# veya
export GOOGLE_API_KEY="AIza..."
```

Anahtar yoksa `optimize.checklist()` yine çalışır. Sadece AI modellerine soru sorma ve otomatik yeniden-yazım kapalı kalır.

## 3. İçerik Kalitesi Skoru

Bir blog yazısını veya landing page metnini E-E-A-T, alıntılanabilirlik, yapı ve güncellik açısından ölçün.

```python
from jev_seo_geo import score

article = """
2026 CRM Karşılaştırması

Bu çalışmada 12 CRM platformunu altı ay boyunca beş kişilik satış ekibiyle test ettik.
...
"""

result = score.content(article, topic="startup CRM")

print(result.eeat)           # deneyim, uzmanlık, otorite, güven
print(result.citation_ready) # AI yanıtında kaynak gösterilme potansiyeli
print(result.structure)      # başlık, tablo, liste gibi yapı sinyalleri
print(result.freshness)      # güncel olma sinyalleri
print(result.overall)        # 0.0-1.0 toplam skor
print(result.suggestions)    # tespit edilen boşluklar
```

### Skorları yorumlama

| Skor | Anlamı | Öncelik |
|---:|---|---|
| 0.00-0.39 | Zayıf, AI kaynak olarak seçmeyebilir | Yeniden yapılandır |
| 0.40-0.64 | Temel yeterlilik, net eksikler var | Hedefli iyileştir |
| 0.65-0.79 | İyi temel, rakip analizi ile geliştir | Optimize et |
| 0.80-1.00 | Güçlü sinyaller | Güncel tut ve probe et |

Bu skorlar yönlendirme içindir, Google veya herhangi bir AI sağlayıcısının resmi sıralaması değildir.

## 4. Önce Checklist, Sonra Rewrite

En güvenli akış önce Jev ile boşlukları tespit etmek, sonra editoryal kontrolle düzeltmektir.

```python
from jev_seo_geo import optimize

plan = optimize.checklist(
    "CRM iş için önemlidir. En iyisini seçin.",
    topic="startup CRM",
)

for item in plan:
    print(f"[{item['priority']}] {item['issue']}")
    print(f"Yapılacak: {item['action']}")
    print(f"Örnek: {item['example']}")
```

Tipik çıktılar:
- Yazar biyografisi ve uzmanlık ekle.
- İddiaları veri, metodoloji ve kaynak ile destekle.
- H2/H3 başlıkları, karşılaştırma tablosu ve SSS ekle.
- Eski tarihleri ve istatistikleri güncelle.

### Otomatik yeniden-yazım

Bir LLM anahtarı tanımlıysa `rewrite()` aynı akışta teşhis eder, metni iyileştirir ve yeniden skorlar.

```python
result = optimize.rewrite(
    text="CRM iş için önemlidir. En iyisini seçin.",
    topic="startup CRM",
    focus="all",
)

print("Önce:", result.before.overall)
print("Sonra:", result.after.overall if result.after else "LLM anahtarı yok")
print("Fark:", result.improvement)
print(result.rewritten)
```

`focus` seçenekleri:
- `all`: tüm boşlukları ele alır.
- `eeat`: yazar deneyimi, uzmanlık ve güven sinyalleri.
- `citation`: veri, kaynak, metodoloji ve kaynak gösterilme potansiyeli.
- `structure`: başlıklar, listeler, tablolar, SSS.
- `freshness`: tarih, terim ve güncel bilgi.

> Otomatik rewrite taslaktır. Uydurulmuş sayı, kaynak veya uzmanlık iddiası yayınlamayın. Metni yayın öncesi insan editoryal doğrulamasından geçirin.

## 5. Başlık Arena

Başlık varyasyonlarını hedef niyete göre sıralayın.

```python
from jev_seo_geo import arena

results = arena.titles(
    [
        "10 Best CRM Tools for Small Business in 2026",
        "CRM Comparison: HubSpot vs Salesforce vs Pipedrive",
        "How to Choose a CRM: Complete Buyer's Guide",
        "We Tested 10 CRMs For 6 Months. Here's What We Found.",
    ],
    intent="startup için CRM araştıran karar verici",
)

for item in results:
    print(item.rank, item.score, item.strengths, item.title)
```

Arena; özgüllük, tıklama değeri, alıntılanabilirlik ve otorite sinyallerini kıyaslar. Bu bir sıralama garantisi değil, alternatifler arasında karar destek aracıdır.

## 6. AI Marka Görünürlüğü Probe

Bu özellik, aynı soruyu seçtiğiniz AI modellerine sorar ve marka adı yanıtın içinde geçiyor mu kontrol eder.

```python
from jev_seo_geo import probe

report = probe.brand(
    brand="Vercel",
    queries=[
        "best platform for deploying Next.js apps",
        "alternatives to Heroku for frontend hosting",
    ],
    models=["openai", "anthropic", "google"],
)

print(report.mention_rate)
print(report.avg_rank)
for result in report.results:
    print(result.model, result.mentioned, result.rank, result.context)
```

Önemli sınırlar:
- AI yanıtları zamana, bölgeye, modele ve prompt'a göre değişir.
- Probe, gözlemdir. Marka görünürlüğünü garanti etmez.
- Prompt setini sektörünüzün gerçek müşteri sorularından üretin.
- Aynı sorguları düzenli aralıklarla tekrar ederek trend oluşturun.

## 7. Rakip Gap Analizi

```python
from jev_seo_geo import gap

report = gap.analyze(
    brand_name="Pipedrive",
    competitors=["HubSpot", "Salesforce"],
    queries=[
        "best CRM for sales teams",
        "easiest CRM to set up",
        "CRM with best API",
    ],
)

print(report.summary)
for recommendation in report.recommendations:
    print("-", recommendation)
```

Bu rapor, hangi markanın seçilen prompt setinde daha çok anıldığını gösterir. Ardından içerik gap'lerini ele almak için `score.content()` ve `optimize.checklist()` kullanın.

## 8. Önerilen İş Akışı

1. Hedef müşteri sorularından 20-50 query oluşturun.
2. `probe.brand()` ile mevcut görünürlüğü ölçün.
3. En az anıldığınız konuları belirleyin.
4. O konulardaki sayfaları `score.content()` ile ölçün.
5. `optimize.checklist()` ile editoryal görev listesi çıkarın.
6. İnsan denetimiyle güncelleyin, kaynakları doğrulayın.
7. Başlık alternatiflerini `arena.titles()` ile test edin.
8. 2-4 hafta sonra aynı probe setiyle tekrar ölçün.

## 9. Güvenli ve Dürüst Kullanım

- Sahte referans, istatistik, müşteri hikayesi veya uzmanlık iddiası üretmeyin.
- Otomatik rewrite çıktısını doğrudan yayınlamayın.
- Sağlık, hukuk, finans gibi yüksek riskli alanlarda alan uzmanı incelemesi kullanın.
- Skorları kesin sıralama veya model garantisi gibi sunmayın.
