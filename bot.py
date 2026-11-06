import os
import json
import urllib.request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# حفظ حالات المستخدمين
user_data = {}

# ⚠️ ضع هنا الـ ID الشخصي الخاص بك لتستقبل عليه إشعارات الدفع
ADMIN_ID = 8684915103

PRICE_PER_CHAPTER = 4 
VODAFONE_CASH_NUM = "01129549934" 

def ask_ai(prompt_text):
    try:
        # اتصال مباشر وسريع بالذكاء الاصطناعي بدون مكتبات خارجية
        url = "https://pollinations.ai"
        data = {
            "messages": [
                {"role": "system", "content": "أنت خبير لغة جافا سكريبت ومساعد لطلاب الصف الأول الثانوي في مصر على منصة Qureo التعليمية. قم بتقديم الأكواد والحلول النموذجية للتدريبات بشكل منسق وجاهز للنسخ في المنصة."},
                {"role": "user", "content": prompt_text}
            ],
            "model": "openai"
        }
        req = urllib.request.Request(url, method="POST")
        req.add_header("Content-Type", "application/json")
        response = urllib.request.urlopen(req, data=json.dumps(data).encode("utf-8"), timeout=15)
        return response.read().decode("utf-8")
    except:
        return "عذراً، محرك الحلول مضغوط حالياً، من فضلك أعد إرسال الرسالة السابقة."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 أهلاً بك في بوت حل تدريبات جافا سكريبت لمنصة Qureo التعليمية! 💻\n\n"
        f"💵 تكلفة حل الفصل الواحد هي {PRICE_PER_CHAPTER} جنيه فقط.\n"
        "يرجى كتابة عدد الفصول التي تريد حلها الآن (اكتب الرقم مباشرة، مثلاً: 1 أو 2)."
    )
    user_data[update.effective_user.id] = {'step': 'get_chapters'}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_data:
        return

    step = user_data[user_id].get('step')

    if step == 'get_chapters':
        chapters_count = int(text) if text.isdigit() else 1
        total_price = chapters_count * PRICE_PER_CHAPTER
        user_data[user_id]['chapters_count'] = chapters_count
        user_data[user_id]['step'] = 'wait_payment'
        
        await update.message.reply_text(
            f"📊 طلبك الحالي: حل ({chapters_count}) فصول من منصة كيريو.\n"
            f"💰 إجمالي السعر المطلوب: {total_price} جنيه مصري.\n\n"
            f"📱 يرجى تحويل المبلغ إلى رقم فودافون كاش التالي:\n"
            f"{VODAFONE_CASH_NUM}\n\n"
            f"⚠️ بعد تحويل الأموال، يرجى إرسال صورة إيصال التحويل هنا لتفعيل حسابك والبدء في الحل."
        )
        return

    if step == 'activated':
        user_data[user_id]['step'] = 'solving_process'
        await update.message.reply_text(
            "🔑 تم تأكيد الدفع بنجاح من قبل الإدارة!\n"
            "يرجى الآن إرسال بيانات حسابك على منصة كيريو (Qureo) بالصيغة التالية:\n\n"
            "اسم المستخدم:\n"
            "كلمة المرور:"
        )
        return

    if step == 'solving_process':
        await update.message.reply_text("📥 جاري استخراج أكواد الجافا سكريبت النموذجية للمنصة... ⏳")
        solution = ask_ai(text)
        await update.message.reply_text(f"📝 إليك الحلول الجاهزة لنسخها:\n\n{solution}")
        user_data[user_id]['step'] = 'activated' 

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data and user_data[user_id].get('step') == 'wait_payment':
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=f"💰 تحويل جديد من الطالب: {user_id}\n"
                    f"للتفعيل أرسل للبوت:\n/activate {user_id}"
        )
        await update.message.reply_text("📥 تم استلام إيصال التحويل! جاري مراجعته وتفعيل حسابك فوراً.")

async def activate_user(update: Update, context: ContextTypes.DEFAULT_TYPE):if update.effective_user.id == ADMIN_ID:
        try:
            target_id = int(context.args[0])
            user_data[target_id]['step'] = 'activated'
            await context.bot.send_message(
                chat_id=target_id, 
                text="✅ تم تأكيد دفعك! من فضلك أرسل أي رسالة ليطلب منك البوت بيانات الحساب ويبدأ الحل فوراً!"
            )
            await update.message.reply_text("👍 تم تفعيل الطالب.")
        except:
            await update.message.reply_text("خطأ في الأمر. اكتبه هكذا: /activate 123456")

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate_user))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    app.run_polling()

if name == 'main':
    main()
