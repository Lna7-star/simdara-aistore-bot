# Ai STORE KH - Telegram Shop Bot

Bot លក់គណនី ChatGPT Plus, Gemini Plus ដូចក្នុង Screenshot របស់ Lim។
មានផលិតផល, ស្តុក, សមតុល្យ, ដាក់ប្រាក់ ABA / Wing / USDT, ទិញអូតូផ្ញើ Gmail + Password ភ្លាម។

## 1. បង្កើត Bot (5 នាទី)

1. បើក Telegram រក `@BotFather`
2. វាយ `/newbot` -> ដាក់ឈ្មោះ -> ដាក់ username បញ្ចប់ដោយ `bot`
3. ចម្លង **Token** ដែល BotFather ឲ្យ
4. រក `@userinfobot` វាយ `/start` ដើម្បីយក **User ID** របស់អ្នក (សម្រាប់ Admin)

## 2. ដំឡើងនៅលើកុំព្យូទ័រ

ត្រូវមាន Python 3.10 ឬថ្មីជាងនេះ។

```bash
# ចូល Folder
cd telegram-store-bot

# ដំឡើង Library
pip install -r requirements.txt

# បង្កើត .env
cp .env.example .env
```

បើក File `.env` ដោយ Notepad / VS Code ហើយបំពេញ៖

```
BOT_TOKEN=Token ពី BotFather
ADMIN_IDS=User ID របស់អ្នក
ABA_NAME=ឈ្មោះ ABA របស់អ្នក
ABA_ACCOUNT=លេខគណនី ABA
WING_NUMBER=លេខ Wing
USDT_ADDRESS=Address USDT TRC20
```

## 3. ដំណើរការ Bot

```bash
python bot.py
```

បើឃើញ `✅ Bot កំពុងដំណើរការ...` មានន័យថាជោគជ័យ។ បើក Telegram រក Bot របស់អ្នក វាយ `/start`។

## 4. របៀបប្រើជា Admin

វាយ `/admin` ក្នុង Bot ដើម្បីមើល៖ អ្នកប្រើសរុប, Order, លក់បានសរុប, Topup រង់ចាំ, បញ្ជីផលិតផល និង ID។

### បន្ថែមផលិតផលថ្មី
```
/addproduct ChatGPT Plus 1M | 6.31 | Gmail ថ្មី ប្រើបានពេញលេញ
```
ទម្រង់៖ `/addproduct ឈ្មោះ | តម្លៃ | ការពិពណ៌នា`

ផលិតផលដើមមានរួចហើយ៖
- Chatgpt plus 1M (Google pay) Gmail NW - $6.31
- Gemini Plus 12M (Credit Card) - $1.75
- Chatgpt plus 12M (Google pay) - $45.00

### បន្ថែមស្តុក
```
/addstock
```
Bot នឹងសួរ ID ផលិតផល រួចសួរបន្ទាត់ស្តុក។ ផ្ញើជាបន្ទាត់ៗ ទម្រង់ `email:password`៖
```
test1@gmail.com:pass123
test2@gmail.com:pass456
```
មួយបន្ទាត់ = 1 គណនី។ លក់បាន 1 Bot លុប 1 ចេញពីស្តុកអូតូ។

### អនុម័តដាក់ប្រាក់
ពេលអតិថិជនដាក់ប្រាក់ Admin នឹងទទួលសារមានប៊ូតុង **✅ Approve / ❌ Reject**។ ចុច Approve លុយនឹងចូលសមតុល្យអតិថិជនភ្លាម។

ឬបន្ថែមលុយដោយផ្ទាល់៖
```
/approve 123456789 10
```
មានន័យថាបន្ថែម $10 ឲ្យ User ID 123456789។

មើល Topup រង់ចាំ៖ `/pending`

## 5. ដំណើរការទិញរបស់អតិថិជន

1. `/start` -> **ស្វែងរក Products**
2. ចុចផលិតផល -> ឃើញតម្លៃ និងស្តុក
3. ចុច **ទិញឥឡូវនេះ**
4. បើលុយមិនគ្រប់ Bot ប្រាប់ឲ្យដាក់ប្រាក់មុន
5. បើលុយគ្រប់ Bot កាត់លុយ ហើយផ្ញើ Gmail + Password ភ្លាម

## 6. ដាក់ប្រាក់របស់អតិថិជន

1. ចុច **ដាក់ប្រាក់ក្នុងគណនី**
2. ជ្រើស ABA KHQR / Wing / USDT
3. វាយចំនួនលុយ ឧទាហរណ៍ `10`
4. បង់តាមព័ត៌មានដែល Bot បង្ហាញ ហើយរង់ចាំ Admin Approve

## 7. ដាក់ Bot ឲ្យដំណើរការ 24/7

កុំព្យូទ័រអ្នកបិទ Bot នឹងឈប់។ ដើម្បីដំណើរការ 24/7 ត្រូវដាក់លើ Server៖

**វិធីងាយ៖ Railway / Render**
- Upload Code នេះទៅ GitHub
- បង្កើត Project ថ្មីក្នុង Railway -> Deploy from GitHub
- ដាក់ Environment Variables ដូចក្នុង `.env`
- ដាក់ Start Command៖ `python bot.py`

**វិធី VPS (Contabo / DigitalOcean ~$5/ខែ)**
```bash
sudo apt update && sudo apt install python3 python3-pip -y
pip install -r requirements.txt
# ដំណើរការជា Service ដោយ systemd ឬ screen
nohup python3 bot.py &
```

## សុវត្ថិភាព

- កុំចែករំលែក `BOT_TOKEN` និង File `.env` ឲ្យអ្នកណា
- កុំ Upload File `.env` ទៅ GitHub
- មានតែ `ADMIN_IDS` ទេដែលប្រើ `/admin`, `/addstock`, `/approve` បាន
- Backup File `shop.db` ជាប្រចាំ ព្រោះវាមានស្តុក និង Order ទាំងអស់

## ឯកសារក្នុង Folder នេះ

- `bot.py` - Code Bot ទាំងមូល
- `requirements.txt` - Library ដែលត្រូវការ
- `.env.example` - គំរូ Config
- `README.md` - File នេះ
- `shop.db` - នឹងបង្កើតអូតូពេលដំណើរការលើកទី 1

## ចំណាំ

គណនី ChatGPT / Gemini ដែលលក់ថោកៗ ជារឿយៗអាចត្រូវបិទដោយ Google / OpenAI។
សូមប្រាប់អតិថិជនឲ្យច្បាស់ពីការធានា ឧទាហរណ៍ ធានា 1 ខែ បើបិទប្តូរថ្មីឲ្យ។
