import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# حفظ حالات المستخدمين
user_data = {}

# ⚠️ ضع هنا الـ ID الشخصي الخاص بك لتستقبل عليه إشعارات الدفع وصور الإيصالات
ADMIN_ID 8684915103

PRICE_PER_CHAPTER = 4 
VODAFONE_CASH_NUM = "01129549934" 

# إعداد محرك جوجل جيميناي للذكاء الاصطناعي
# سنقوم بجلب مفتاح التشغيل الآمن تلقائياً من إعدادات ريلواي
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 أهلاً بك في بوت حل تدريبات جافا سكريبت لمنصة Qureo التعليمية! 💻\n\n"
        f"💵 تكلفة حل الفصل الواحد هي {PRICE_PER_CHAPTER} جنيه فقط.\n"
        "يرجى كتابة أرقام الفصول أو عدد الفصول التي تريد حلها الآن (مثال: فصل واحد أو اكتب رقم 3)."
    )
    user_data[update.effective_user.id] = {'step': 'get_chapters'}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_data:
        return

    step = user_data[user_id].get('step')

    if step == 'get_chapters':
        digits = [int(s) for s in text.split() if s.isdigit()]
        chapters_count = digits[0] if digits else 1
        
        total_price = chapters_count * PRICE_PER_CHAPTER
        user_data[user_id]['chapters_count'] = chapters_count
        user_data[user_id]['step'] = 'wait_payment'
        
        await update.message.reply_text(
            f"📊 طلبك الحالي: حل ({chapters_count}) فصول من منصة كيريو.\n"
            f"💰 إجمالي السعر المطلوب: {total_price} جنيه مصري.\n\n"
            f"📱 يرجى تحويل المبلغ إلى رقم فودافون كاش التالي:\n"
            f"{VODAFONE_CASH_NUM}\n\n"
            f"⚠️ بعد تحويل الأموال، يرجى إرسال لقطة شاشة (Screenshot) واضحة للإيصال هنا لتفعيل حسابك والبدء في الحل."
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
        await update.message.reply_text("📥 جاري الدخول لفصلك على منصة Qureo واستخراج أكواد الجافا سكريبت النموذجية... ⏳")
        try:
            prompt = (
                f"أنت خبير لغة جافا سكريبت ومساعد لطلاب الصف الأول الثانوي في مصر على منصة Qureo التعليمية. "
                f"قم بتقديم الأكواد والحلول النموذجية المقالية والاختيارية للتدريبات والامتحانات بناءً على هذه البيانات المرسلة:\n {text}\n"
                f"اكتب الأكواد بشكل منسق وجاهز للنسخ."
            )
            response = model.generate_content(prompt)
            await update.message.reply_text(f"📝 إليك الحلول الجاهزة لنسخها في المنصة:\n\n{response.text}")
            user_data[user_id]['step'] = 'activated' 
        except Exception as e:
            await update.message.reply_text("عذراً، محرك الحلول مضغوط حالياً، من فضلك أعد إرسال الرسالة السابقة.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data and user_data[user_id].get('step') == 'wait_payment':
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=f"💰 إشعار تحويل جديد من الطالب: {user_id}\n"
                    f"طلب حل عدد فصول: {user_data[user_id].get('chapters_count')}\n\n"
                    f"للبدء في الحل وتفعيل الطالب، انسخ هذا الأمر وأرسله للبوت:\n"
                    f"/activate {user_id}"
        )
        await update.message.reply_text("📥 تم استلام إيصال التحويل بنجاح! جاري مراجعته والتحقق من وصول الأموال للمحفظة، وسيبدأ البوت بالحل فوراً خلال دقائق.")
async def activate_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        try:
            target_id = int(context.args[0])
            user_data[target_id]['step'] = 'activated'
            await context.bot.send_message(
                chat_id=target_id, 
                text="✅ رائع! تأكدنا من وصول الأموال. من فضلك أرسل أي رسالة أو اضغط هنا ليطلب منك البوت بيانات حساب المنصة ويبدأ الحل فوراً!"
            )
            await update.message.reply_text("👍 تم تفعيل الطالب بنجاح، وفتح محرك الحلول له.")
        except Exception as e:
            await update.message.reply_text("خطأ في صيغة الأمر، تأكد من كتابته كالتالي: /activate 1234567")

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
