# jev-seo-geo Kullanım Kılavuzu

Bu kütüphane API yanıtlarında marka adının geçmesini gözlemler, verilen metne sezgisel puan verir ve insan incelemesi gerektiren taslaklar üretir. Google sıralaması veya tüketici ChatGPT sıralaması ölçmez. Perplexity entegrasyonu, canlı web tarama, sayfa indirme ve crawler yoktur. URL yalnızca bağlamdır.

## Kurulum

PyPI yayını doğrulanmadığından kaynak depoyu kullanın:

```sh
pip install "git+https://github.com/avgon/jev-seo-geo.git"
```

Python 3.9+ hedeflenir; bu çalışmada yalnızca 3.13 üzerinde test yapıldı. Yerel test: `python -m unittest discover -s tests -v`. Ağ çağrısı yapmayan eksiksiz örnekler README içinde bulunur.

## Kimlik bilgileri ve ücret

Puanlama, checklist ve başlık arena için Jev anahtarı gerekir. Marka probe ve gap için yalnızca üretken model anahtarı gerekir, Jev gerekmez. Otomatik rewrite için Jev ile birlikte üretken sağlayıcı veya callback gerekir. Checklist, üretken model anahtarı olmadan çalışır ama Jev anahtarı olmadan çalışmaz.

`JevClient(api_key=..., model=...)` ve `LLMProber(keys={...}, models={...})` ile açık yapılandırma tercih edin. Yerleşik sağlayıcı adları `openai`, `anthropic`, `google` değerleridir. Bilinmeyen adlar reddedilir. Model kimliklerini sağlayıcınızın desteklediği değerlerle belirleyin. Varsayılan modelin hâlâ kullanılabilir olduğu garanti edilmez.

Argüman verilmezse ilgili ortam değişkenleri okunabilir: `TYPESAFE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`. `LLMProber(keys={})` ortamdan anahtar aramayı kapatır. Testler gerçek anahtar kullanmaz. Gerçek çağrılar ücretli olabilir ve metninizi harici sağlayıcıya gönderir. Gizli veya müşteri verisini izinsiz göndermeyin, anahtarları rapora/depoya koymayın.

## Marka ve rakip karşılaştırması

Aşağıdaki örnek tamamen yereldir:

```python
from jev_seo_geo import probe, gap

class YerelOrnek:
    available_models = ["yerel"]
    models = {"yerel": "ornek-v1"}
    def query(self, prompt, provider, timeout=30):
        return "1. ÖrnekMarka\n2. RakipMarka"

p = YerelOrnek()
report = probe.brand(brand="ÖrnekMarka", queries=["Küçük ekip için hangi araçlar var?"], prober=p)
for item in report.results:
    print(item.status, item.mentioned, item.rank, item.timestamp)
print(report.mention_rate, report.success_count, report.error_count)

comparison = gap.analyze(
    brand_name="ÖrnekMarka", competitors=["RakipMarka"],
    queries=["Küçük ekip için hangi araçlar var?"], prober=p, samples=2,
)
print(comparison.summary)
```

Her benzersiz soru/sağlayıcı/örnek bir kez üretilir; tüm markalar aynı yanıtta değerlendirilir. Marka adını soruya eklemek ölçümü yanlılaştırabilir. Tarafsız ve sabit soru seti kullanın.

Hata, markanın yokluğu değildir. Başarısız gözlemde `mentioned=None`, `rank=None` olur; oran yalnızca başarılı yanıtlardan hesaplanır. Hiç başarılı yanıt yoksa `mention_rate=None` olur. `complete`, `partial`, `failed` durumlarını ve hata sayılarını inceleyin. `rank` yalnızca marka numaralı listenin başında açıkça bulunduğunda gerçek liste numarasıdır; genel anılma öneri veya tavsiye kanıtı değildir. Unicode sözcük sınırı kullanılır, bitişik CJK metinlerde sözcük ayrıştırma ve takma ad çözümleme yapılmaz.

## Metin, başlık ve checklist

Gerçek Jev istemcisiyle kullanacağınız çağrılar:

```python
# j: yapılandırılmış JevClient veya açık yerel test nesnesi
# from jev_seo_geo import score, arena, optimize
# result = score.content("Mevcut metin", topic="ekip araçları", client=j)
# ranked = arena.titles(["Araç seçim rehberi", "Ekip araçları nasıl karşılaştırılır?"], client=j)
# tasks = optimize.checklist("Mevcut metin", focus="citation", jev=j)
```

`focus`: `all`, `eeat`, `citation`, `structure`, `freshness`. Geçersiz değer reddedilir. Jev puanları resmî Google E-E-A-T puanı, doğruluk kontrolü veya SEO başarı tahmini değildir. Ham yapı puanı 0..2 ölçeğindedir ve daima ikiye bölünür. Eksik veya bozuk Jev alanları sessizce sıfır yapılmaz, hata verir. Eşit başlık puanları aynı sırayı alır.

## Rewrite ve rapor

`optimize.rewrite(text, jev=j, prober=p)` otomatik sağlayıcı kullanabilir; `generator=fonksiyon` ile prompt alan ve boş olmayan metin döndüren kendi üreticinizi bağlayabilirsiniz. Callback varsa sağlayıcı yerine o kullanılır.

- `no_provider`: üretken sağlayıcı yok; checklist vardır.
- `generated`: taslak üretildi ve tekrar puanlandı, doğrulanmış değildir.
- `generation_failed`: üretim başarısız veya sonuç geçersiz.
- `scoring_failed`: taslak korundu ancak son puan alınamadı.

Başlangıç puanlaması başarısızsa çağrı hata verir. `error` yalnızca güvenli hata kategorisidir. `improvement`, sezgisel puan farkıdır; SEO artışı değildir. `human_review_required` ve `unverified_draft` her zaman açıktır. `unresolved_placeholders` içindeki `[VERIFY: ...]` alanlarını çözün. Hiç alan olmaması doğrulama yapıldığı anlamına gelmez. İstatistik, kaynak, tarih, uzmanlık ve müşteri iddialarını insan editör doğrulamalıdır.

`audit.run(brand, domain, category, competitors, content=..., jev=j, prober=p)` birleşik rapor üretir. `report.save("audit.html")` yerel HTML yazar. Durum ve `errors` alanına bakın; başarısız API çağrıları başarılı denetim sayılmaz. Atlanan bölümler ölçülmüş sayılmaz.

## Kapsam sınırları

Metin, başlık, soru ve yakalanan sağlayıcı yanıtı için 12.000 karakter sınırı vardır. Fazlası açıkça reddedilir; sessiz kesme, parça metni yeniden yazma ve chunking yoktur. Üretilen taslak sınırı aşarsa korunur ancak `scoring_failed` olur. Sağlayıcı çıktı limitleri yanıtı erken bitirebilir; tamlık garanti edilmez. Site genelini analiz etmez.

Karşılaştırma yalnızca örneklenen yanıtlardaki farkı gösterir. Rakibin neden daha çok anıldığını nedensel olarak açıklamaz. Bu çalışmada gerçek sağlayıcı başarısı veya SEO artışı doğrulanmadı.
