import logging
import math
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from faker import Faker

# --- 1. CONFIGURATION ---
BOT_TOKEN = "YOUR_BOT_TOKEN"  # <<<--- আপনার আসল টোকেনটি এখানে বসান

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 2. DATA: COMPREHENSIVE COUNTRY & LOCALE MAPPING ---
COUNTRY_LOCALES = {
    "Argentina": "es_AR", "Australia": "en_AU", "Austria": "de_AT", "Azerbaijan": "az_AZ",
    "Bangladesh": "bn_BD", "Belgium (Dutch)": "nl_BE", "Belgium (French)": "fr_BE",
    "Brazil": "pt_BR", "Bulgaria": "bg_BG", "Canada": "en_CA", "Chile": "es_CL",
    "China": "zh_CN", "Colombia": "es_CO", "Croatia": "hr_HR", "Cyprus": "el_CY",
    "Czech Republic": "cs_CZ", "Denmark": "da_DK", "Egypt (Arabic)": "ar_EG",
    "Estonia": "et_EE", "Finland": "fi_FI", "France": "fr_FR", "Georgia": "ka_GE",
    "Germany": "de_DE", "Greece": "el_GR", "Hungary": "hu_HU", "Iceland": "is_IS",
    "India (English)": "en_IN", "India (Hindi)": "hi_IN", "India (Tamil)": "ta_IN",
    "Indonesia": "id_ID", "Iran (Farsi)": "fa_IR", "Ireland": "en_IE", "Israel (Hebrew)": "he_IL",
    "Italy": "it_IT", "Japan": "ja_JP", "Kazakhstan": "kk_KZ", "Latvia": "lv_LV",
    "Lithuania": "lt_LT", "Luxembourg": "fr_LU", "Malaysia": "ms_MY", "Mexico": "es_MX",
    "Moldova": "ro_MD", "Nepal": "ne_NP", "Netherlands": "nl_NL", "New Zealand": "en_NZ",
    "Nigeria": "en_NG", "Norway": "no_NO", "Pakistan (Urdu)": "ur_PK", "Peru": "es_PE",
    "Philippines": "fil_PH", "Poland": "pl_PL", "Portugal": "pt_PT", "Romania": "ro_RO",
    "Russia": "ru_RU", "Saudi Arabia (Arabic)": "ar_SA", "Serbia": "sr_RS",
    "Singapore": "en_SG", "Slovakia": "sk_SK", "Slovenia": "sl_SI", "South Africa": "en_ZA",
    "South Korea": "ko_KR", "Spain": "es_ES", "Sweden": "sv_SE", "Switzerland (German)": "de_CH",
    "Switzerland (French)": "fr_CH", "Taiwan": "zh_TW", "Thailand": "th_TH", "Turkey": "tr_TR",
    "Ukraine": "uk_UA", "United Arab Emirates": "ar_AE", "United Kingdom": "en_GB",
    "United States": "en_US", "Vietnam": "vi_VN"
}
ITEMS_PER_PAGE = 18

# --- 3. HELPER FUNCTIONS ---

def create_country_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """Creates a paginated inline keyboard for country selection."""
    sorted_countries = sorted(COUNTRY_LOCALES.keys())
    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    page_countries = sorted_countries[start_index:end_index]
    
    keyboard = []
    row = []
    for country in page_countries:
        locale_code = COUNTRY_LOCALES[country]
        row.append(InlineKeyboardButton(country, callback_data=f"LOC_{locale_code}"))
        if len(row) == 2: keyboard.append(row); row = []
    if row: keyboard.append(row)
    
    pagination_row = []
    if page > 0: pagination_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"PAGE_{page-1}"))
    if end_index < len(sorted_countries): pagination_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"PAGE_{page+1}"))
    if pagination_row: keyboard.append(pagination_row)
        
    return InlineKeyboardMarkup(keyboard)

def generate_names_list_safely(locale_code: str, gender: str) -> list[str]:
    """
    [REBUILT FOR RELIABILITY] This function safely generates names, falling back to
    generic names if gender-specific ones are not available for a locale like 'bn_BD'.
    """
    try:
        fake = Faker(locale_code)
        names = set()
        
        name_func = fake.name
        if gender == 'male' and hasattr(fake, 'name_male'):
            name_func = fake.name_male
        elif gender == 'female' and hasattr(fake, 'name_female'):
            name_func = fake.name_female
        
        while len(names) < 3:
            names.add(name_func())
            
        return list(names)
    except Exception as e:
        logger.error(f"Failed to generate names for locale '{locale_code}': {e}")
        return ["Generation Failed", "Please Try Another", "Country or Gender"]

# --- 4. TELEGRAM HANDLER FUNCTIONS ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    welcome_message = (
        "✨ **Welcome to the Name Generator Bot!** ✨\n\n"
        "This bot provides culturally-appropriate fake names from countries around the globe. 🌎\n\n"
        "**📚 How to Use:**\n"
        "1. Click '🚀 Start Generating Names'.\n"
        "2. Select a country from the list. 🗺️\n"
        "3. Choose the desired gender. 🚻\n"
        "4. Receive **3 unique names** you can click-to-copy! 📝"
    )
    keyboard = [[InlineKeyboardButton("🚀 Start Generating Names", callback_data="PAGE_0")]]
    await update.message.reply_text(welcome_message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def country_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the paginated list of countries."""
    query = update.callback_query
    await query.answer()
    page = int(query.data.split('_')[1])
    await query.edit_message_text(f"👇 **🗺️ Please select a country (Page {page + 1}):**", reply_markup=create_country_keyboard(page=page), parse_mode='Markdown')

async def gender_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays gender selection buttons."""
    query = update.callback_query
    await query.answer()
    locale_code = query.data.split('_', 1)[1]
    country_name = next((country for country, loc in COUNTRY_LOCALES.items() if loc == locale_code), "Selected Region")
    
    keyboard = [
        [InlineKeyboardButton("🚹 Male", callback_data=f"GEN_{locale_code}_male")],
        [InlineKeyboardButton("🚺 Female", callback_data=f"GEN_{locale_code}_female")],
        [InlineKeyboardButton("🚻 Any", callback_data=f"GEN_{locale_code}_any")],
        [InlineKeyboardButton("⬅️ Back to Countries", callback_data='PAGE_0')],
    ]
    await query.edit_message_text(
        f"✨ **Country:** {country_name}\n\n**❓ Please select the gender for the names:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def name_generation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """**[THE FINAL FIX]** This is the core function, now with correct parsing logic."""
    query = update.callback_query
    await query.answer(text="✅ Processing your request...")

    try:
        # --- THE CRITICAL FIX IS HERE ---
        # The previous code was splitting "bn_BD" incorrectly. This new code parses it correctly.
        parts = query.data.split('_')
        gender = parts[-1]
        locale_code = '_'.join(parts[1:-1])  # This correctly re-joins 'bn' and 'BD' into 'bn_BD'

        logger.info(f"Correctly parsed: locale='{locale_code}', gender='{gender}'")

        names = generate_names_list_safely(locale_code, gender)
        
        country_name = next((country for country, loc in COUNTRY_LOCALES.items() if loc == locale_code), "Selected Region")
        
        response_text = (
            f"**Culture:** {country_name} (`{locale_code}`)\n"
            f"**Gender:** {gender.capitalize()}\n"
            f"--- **✅ Here are 3 unique names:** ---\n"
            f"1. `{names[0]}`\n"
            f"2. `{names[1]}`\n"
            f"3. `{names[2]}`"
        )
        
        keyboard = [
            [InlineKeyboardButton(f"➕ Generate 3 More {gender.capitalize()}", callback_data=query.data)],
            [InlineKeyboardButton("↩️ Change Gender", callback_data=f"LOC_{locale_code}")],
            [InlineKeyboardButton("⬅️ Back to Countries", callback_data='PAGE_0')],
        ]
        
        await query.message.reply_text(
            text=response_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"A critical error occurred in name_generation_callback: {traceback.format_exc()}")
        await query.message.reply_text("❌ A critical error occurred. The developer has been notified. Please try /start again.")

# --- 5. MAIN FUNCTION ---

def main() -> None:
    """Initializes and starts the bot."""
    if BOT_TOKEN == "YOUR_BOT_TOKEN":
        print("\nFATAL ERROR: Please replace 'YOUR_BOT_TOKEN' in the script with your actual bot token.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Register all handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(country_selection_callback, pattern=r'^PAGE_\d+$'))
    application.add_handler(CallbackQueryHandler(gender_selection_callback, pattern=r'^LOC_.+$'))
    application.add_handler(CallbackQueryHandler(name_generation_callback, pattern=r'^GEN_.+$'))
    
    print("The bot is now running perfectly. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()