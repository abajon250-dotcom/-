import os
import shutil
from config import LANDING_STORAGE_PATH, LANDING_BASE_URL

DEFAULT_TEMPLATES = {
    'news': '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} — Новости</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
        body { background: #f0f2f5; display: flex; justify-content: center; padding: 20px; }
        .card { max-width: 1100px; width: 100%; background: white; border-radius: 30px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); }
        .card-img { width: 100%; height: 400px; background-image: url('{{image_url}}'); background-size: cover; background-position: center; }
        .card-content { padding: 40px; }
        .meta { display: flex; gap: 20px; color: #6b7280; margin-bottom: 15px; font-size: 14px; }
        .title { font-size: 2.5rem; font-weight: 800; color: #111827; margin-bottom: 20px; }
        .desc { font-size: 1.2rem; line-height: 1.6; color: #2d3a4b; border-left: 4px solid #3b82f6; padding-left: 20px; margin-bottom: 30px; }
        .btn { display: inline-block; background: #3b82f6; color: white; font-weight: 600; padding: 14px 40px; border-radius: 50px; text-decoration: none; transition: 0.3s; }
        .btn:hover { background: #2563eb; transform: translateY(-2px); }
        .footer { margin-top: 30px; border-top: 1px solid #e5e7eb; padding-top: 20px; display: flex; justify-content: space-between; color: #9ca3af; }
    </style>
</head>
<body>
    <div class="card">
        <div class="card-img" style="background-image: url('{{image_url}}');"></div>
        <div class="card-content">
            <div class="meta"><span>📅 {{date}}</span><span>🏷️ {{category}}</span></div>
            <h1 class="title">{{title}}</h1>
            <p class="desc">{{description}}</p>
            <a href="{{offer_link}}" class="btn">{{button_text}}</a>
            <div class="footer"><span>👁️ {{views}} просмотров</span><span>🔗 {{source}}</span></div>
        </div>
    </div>
</body>
</html>''',
    'accident': '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Сводка ДТП — Официальная информация</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Arial', 'Helvetica', sans-serif; background: #f0f2f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .container { max-width: 800px; width: 100%; background: white; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: #b22222; color: white; padding: 20px 25px; border-bottom: 3px solid #ffd700; }
        .header h1 { font-size: 22px; font-weight: 500; letter-spacing: 0.5px; }
        .content { padding: 30px 25px; }
        .info-block { background: #f8faff; border-left: 4px solid #b22222; padding: 15px 20px; margin-bottom: 25px; border-radius: 0 8px 8px 0; }
        .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e0e0e0; }
        .info-row:last-child { border-bottom: none; }
        .info-label { font-weight: 600; color: #2c3e50; }
        .info-value { color: #0b3b5c; font-weight: 500; }
        .video-preview { position: relative; width: 100%; height: 300px; background: #000; border-radius: 12px; overflow: hidden; margin-bottom: 25px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .video-preview img { width: 100%; height: 100%; object-fit: cover; filter: blur(6px); opacity: 0.7; }
        .video-play { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(178,34,34,0.9); color: white; border: none; width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 30px; cursor: pointer; box-shadow: 0 5px 15px rgba(0,0,0,0.4); }
        .video-play::after { content: "▶"; }
        .btn-official { display: inline-block; background: #b22222; color: white; font-weight: 600; font-size: 18px; padding: 16px 40px; border-radius: 50px; text-decoration: none; width: 100%; text-align: center; border: none; cursor: pointer; transition: background 0.2s; box-shadow: 0 8px 20px rgba(178,34,34,0.3); }
        .btn-official:hover { background: #8b1a1a; }
        .footer { background: #f5f5f5; padding: 15px 25px; font-size: 13px; color: #666; display: flex; justify-content: space-between; border-top: 1px solid #ddd; }
        .footer a { color: #b22222; text-decoration: none; }
        .badge { background: #ffd700; color: #b22222; padding: 3px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 Сводка ДТП: <span>Официальная информация</span></h1>
        </div>
        <div class="content">
            <div class="info-block">
                <h2 style="margin-bottom: 15px; font-size: 20px; color: #b22222;">Материалы дела</h2>
                <div class="info-row"><span class="info-label">Протокол:</span><span class="info-value">№ДТП-4829</span></div>
                <div class="info-row"><span class="info-label">Доступ к видеозаписи:</span><span class="info-value">Система видеофиксации</span></div>
                <div class="info-row"><span class="info-label">Дата события:</span><span class="info-value">{{date}}</span></div>
                <div class="info-row"><span class="info-label">Статус:</span><span class="info-value"><span class="badge">Подтверждено ГИБДД</span></span></div>
                <div class="info-row"><span class="info-label">Формат:</span><span class="info-value">Full HD (MP4)</span></div>
            </div>
            <div class="video-preview">
                <img src="{{image_url}}" alt="Превью видео" onerror="this.src='https://source.unsplash.com/featured/?accident,car';">
                <div class="video-play"></div>
            </div>
            <a href="{{offer_link}}" class="btn-official">{{button_text}}</a>
        </div>
        <div class="footer">
            <span>© УГИБДД МВД России</span>
            <a href="#">Политика обработки данных</a>
        </div>
    </div>
</body>
</html>''',
    'covid': '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} — Официальная информация</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Arial', 'Helvetica', sans-serif; background: #f4f7fb; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
        .hospital-card { max-width: 900px; width: 100%; background: white; border-radius: 24px; overflow: hidden; box-shadow: 0 15px 35px rgba(0, 51, 102, 0.2); border: 1px solid #e0e7ef; }
        .hospital-header { background: linear-gradient(135deg, #0057a3 0%, #003d73 100%); color: white; padding: 25px 30px; display: flex; align-items: center; gap: 15px; }
        .hospital-header i { font-size: 40px; background: rgba(255,255,255,0.2); width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
        .hospital-header h1 { font-size: 28px; font-weight: 600; letter-spacing: 0.5px; }
        .hospital-badge { background: #ffd966; color: #003d73; padding: 4px 15px; border-radius: 30px; font-size: 14px; font-weight: 700; margin-left: 15px; }
        .hospital-content { padding: 30px; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px; }
        .info-item { background: #f0f6ff; padding: 15px; border-radius: 16px; border-left: 4px solid #0057a3; }
        .info-label { color: #003d73; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }
        .info-value { font-size: 18px; font-weight: 500; color: #1e293b; }
        .description-block { background: #f8fafc; padding: 20px; border-radius: 16px; margin-bottom: 25px; border: 1px solid #d9e2ef; }
        .description-block p { font-size: 16px; line-height: 1.7; color: #2c3e50; }
        .btn-hospital { display: inline-block; background: #0057a3; color: white; font-weight: 600; font-size: 18px; padding: 16px 40px; border-radius: 60px; text-decoration: none; width: 100%; text-align: center; border: none; cursor: pointer; transition: background 0.2s; box-shadow: 0 8px 20px rgba(0,87,163,0.3); }
        .btn-hospital:hover { background: #003d73; }
        .hospital-footer { margin-top: 25px; border-top: 1px solid #d9e2ef; padding-top: 20px; display: flex; justify-content: space-between; color: #5e6f8d; font-size: 14px; }
        .hospital-footer span i { margin-right: 5px; }
        .emergency { background: #fee2e2; color: #b91c1c; border-radius: 50px; padding: 4px 15px; font-weight: 600; font-size: 13px; }
    </style>
</head>
<body>
    <div class="hospital-card">
        <div class="hospital-header">
            <i>🏥</i>
            <div>
                <h1>Городская клиническая больница №1</h1>
                <span class="hospital-badge">Официальный источник</span>
            </div>
        </div>
        <div class="hospital-content">
            <div class="info-grid">
                <div class="info-item"><div class="info-label">Дата публикации</div><div class="info-value">{{date}}</div></div>
                <div class="info-item"><div class="info-label">Категория</div><div class="info-value">{{category}}</div></div>
            </div>
            <div class="description-block">
                <h2 style="margin-bottom: 15px; color: #003d73;">{{title}}</h2>
                <p>{{description}}</p>
            </div>
            <a href="{{offer_link}}" class="btn-hospital">{{button_text}}</a>
            <div class="hospital-footer">
                <span><i>👁️</i> {{views}} просмотров</span>
                <span><i>🔗</i> {{source}}</span>
                <span class="emergency">🚑 Единый номер: 103</span>
            </div>
        </div>
    </div>
</body>
</html>''',
    'gibdd': '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Госавтоинспекция: Официальный портал</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Arial', 'Helvetica', sans-serif; background: #f0f2f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .container { max-width: 800px; width: 100%; background: white; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: #003c8f; color: white; padding: 20px 25px; border-bottom: 3px solid #ffd600; }
        .header h1 { font-size: 22px; font-weight: 500; letter-spacing: 0.5px; }
        .content { padding: 30px 25px; }
        .info-block { background: #f8faff; border-left: 4px solid #003c8f; padding: 15px 20px; margin-bottom: 25px; border-radius: 0 8px 8px 0; }
        .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e0e0e0; }
        .info-row:last-child { border-bottom: none; }
        .info-label { font-weight: 600; color: #2c3e50; }
        .info-value { color: #0b3b5c; font-weight: 500; }
        .video-preview { position: relative; width: 100%; height: 300px; background: #000; border-radius: 12px; overflow: hidden; margin-bottom: 25px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .video-preview img { width: 100%; height: 100%; object-fit: cover; filter: blur(6px); opacity: 0.7; }
        .video-play { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,60,143,0.9); color: white; border: none; width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 30px; cursor: pointer; box-shadow: 0 5px 15px rgba(0,0,0,0.4); }
        .video-play::after { content: "▶"; }
        .btn-official { display: inline-block; background: #003c8f; color: white; font-weight: 600; font-size: 18px; padding: 16px 40px; border-radius: 50px; text-decoration: none; width: 100%; text-align: center; border: none; cursor: pointer; transition: background 0.2s; box-shadow: 0 8px 20px rgba(0,60,143,0.3); }
        .btn-official:hover { background: #002a6e; }
        .footer { background: #f5f5f5; padding: 15px 25px; font-size: 13px; color: #666; display: flex; justify-content: space-between; border-top: 1px solid #ddd; }
        .footer a { color: #003c8f; text-decoration: none; }
        .badge { background: #ffd600; color: #003c8f; padding: 3px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚔 Госавтоинспекция: <span>Официальный портал</span></h1>
        </div>
        <div class="content">
            <div class="info-block">
                <h2 style="margin-bottom: 15px; font-size: 20px; color: #003c8f;">Материалы дела</h2>
                <div class="info-row"><span class="info-label">Протокол:</span><span class="info-value">№4829-Б</span></div>
                <div class="info-row"><span class="info-label">Доступ к видеозаписи:</span><span class="info-value">ГЛОНАСС/GPS (ограничен)</span></div>
                <div class="info-row"><span class="info-label">Дата события:</span><span class="info-value">{{date}}</span></div>
                <div class="info-row"><span class="info-label">Статус:</span><span class="info-value"><span class="badge">Проверено ГИБДД</span></span></div>
                <div class="info-row"><span class="info-label">Формат:</span><span class="info-value">Full HD (MP4)</span></div>
            </div>
            <div class="video-preview">
                <img src="{{image_url}}" alt="Превью видео" onerror="this.src='https://source.unsplash.com/featured/?accident,car';">
                <div class="video-play"></div>
            </div>
            <a href="{{offer_link}}" class="btn-official">{{button_text}}</a>
        </div>
        <div class="footer">
            <span>© ГУ МВД России по г. Москве</span>
            <a href="#">Политика обработки данных</a>
        </div>
    </div>
</body>
</html>''',
    'max': '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} — MAX Новости</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0b1120; font-family: 'Inter', system-ui, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
        .max-card { max-width: 900px; width: 100%; background: #1e293b; border-radius: 32px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0,255,255,0.3); border: 1px solid #334155; }
        .max-img { width: 100%; height: 350px; background-image: url('{{image_url}}'); background-size: cover; background-position: center; }
        .max-content { padding: 40px; color: #e2e8f0; }
        .max-meta { display: flex; gap: 20px; color: #94a3b8; font-size: 14px; margin-bottom: 15px; }
        .max-title { font-size: 40px; font-weight: 800; color: #38bdf8; margin-bottom: 20px; text-shadow: 0 2px 10px rgba(56,189,248,0.3); }
        .max-desc { font-size: 18px; line-height: 1.6; color: #cbd5e1; background: #0f172a; padding: 20px; border-radius: 16px; border-left: 4px solid #38bdf8; margin-bottom: 30px; }
        .max-btn { display: inline-block; background: #38bdf8; color: #0f172a; font-weight: 700; padding: 16px 48px; border-radius: 50px; text-decoration: none; font-size: 18px; transition: 0.3s; box-shadow: 0 10px 20px -5px #38bdf8; }
        .max-btn:hover { background: #7dd3fc; transform: translateY(-3px); box-shadow: 0 20px 30px -5px #38bdf8; }
        .max-footer { margin-top: 30px; border-top: 1px solid #334155; padding-top: 20px; display: flex; justify-content: space-between; color: #64748b; font-size: 14px; }
        .max-footer span i { color: #38bdf8; }
    </style>
</head>
<body>
    <div class="max-card">
        <div class="max-img" style="background-image: url('{{image_url}}');"></div>
        <div class="max-content">
            <div class="max-meta"><span>📅 {{date}}</span><span>🏷️ MAX Insider</span></div>
            <h1 class="max-title">{{title}}</h1>
            <p class="max-desc">{{description}}</p>
            <a href="{{offer_link}}" class="max-btn">{{button_text}}</a>
            <div class="max-footer"><span><i>👁️</i> {{views}} просмотров</span><span><i>🔗</i> {{source}}</span></div>
        </div>
    </div>
</body>
</html>'''
}

def ensure_template(template_name):
    templates_dir = os.path.join("templates", "landings")
    os.makedirs(templates_dir, exist_ok=True)
    file_path = os.path.join(templates_dir, f"{template_name}.html")
    if not os.path.exists(file_path):
        if template_name in DEFAULT_TEMPLATES:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(DEFAULT_TEMPLATES[template_name])
            print(f"✅ Создан шаблон по умолчанию: {file_path}")
        else:
            raise FileNotFoundError(f"Неизвестный шаблон {template_name}")
    return file_path

def generate_landing(name, template_name, title, description, button_text, offer_link,
                     image_url="https://source.unsplash.com/featured/?news",
                     date="Сегодня", category="Срочные новости", views="1.2k", source="Lenta.ru"):
    ensure_template(template_name)

    template_path = os.path.join("templates", "landings", f"{template_name}.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    replacements = {
        "{{title}}": title,
        "{{description}}": description,
        "{{button_text}}": button_text,
        "{{offer_link}}": offer_link,
        "{{image_url}}": image_url,
        "{{date}}": date,
        "{{category}}": category,
        "{{views}}": views,
        "{{source}}": source
    }
    for key, value in replacements.items():
        html = html.replace(key, value)

    landing_dir = os.path.join(LANDING_STORAGE_PATH, name)
    os.makedirs(landing_dir, exist_ok=True)
    index_path = os.path.join(landing_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"📁 Лендинг сохранён: {index_path}")
    base = LANDING_BASE_URL.rstrip('/')
    return f"{base}/{name}/"