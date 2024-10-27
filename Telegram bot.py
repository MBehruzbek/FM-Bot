import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp
from shazamio import Shazam
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Bot tokeni
TELEGRAM_TOKEN = "7615041295:AAEFRChbRDlnxLVBknPRbv-0FsXHZ5oluEk"

# Shazam va Spotify sozlamalari
shazam = Shazam()
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id="1e5c226e3ee94ba18606ec8ea40e5186",
    client_secret="dbbb1f8890ed48d794ce39b73392e983"
))


# Videodan audio yuklab olish
def download_audio_from_url(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "audio.mp3"


# /start komandasi uchun funksiya
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Salom! Menga Instagram, TikTok, YouTube, Facebook, yoki Likee videosining silkasini yoki qo‘shiq nomini yuboring!",
        reply_markup=main_menu()
    )


# Asosiy menyu tugmalari
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎶 Qo‘shiq nomi bo‘yicha qidirish", callback_data='search_by_name')],
        [InlineKeyboardButton("📹 Video orqali qidirish", callback_data='search_by_video')]
    ]
    return InlineKeyboardMarkup(keyboard)


# Menyudan tanlanganda javob berish
def menu_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    if query.data == 'search_by_name':
        query.edit_message_text("Qo‘shiq nomi yoki ijrochini yuboring:")
        context.user_data['search_mode'] = 'name'
    elif query.data == 'search_by_video':
        query.edit_message_text("Instagram, TikTok, YouTube, Facebook yoki Likee videosi havolasini yuboring:")
        context.user_data['search_mode'] = 'video'


# Foydalanuvchi video havolasini yuborganda
async def identify_song_from_video(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    try:
        audio_file = download_audio_from_url(url)

        # Shazam orqali qo'shiqni aniqlash
        with open(audio_file, 'rb') as file:
            out = await shazam.recognize_song(file.read())

        if out["track"]:
            track = out["track"]
            song_info = f"Qo'shiq: {track['title']}\nIjrochi: {track['subtitle']}\nLink: {track['url']}"
            await update.message.reply_text(song_info)
        else:
            await update.message.reply_text("Afsus, bu qo'shiq topilmadi.")

        os.remove(audio_file)

    except Exception as e:
        await update.message.reply_text(f"Xatolik yuz berdi: {e}")


# Qo‘shiq nomi bo‘yicha qidiruv
def search_song_by_name(update: Update, context: CallbackContext) -> None:
    query = update.message.text
    result = spotify.search(q=query, type="track", limit=5)

    if result['tracks']['items']:
        songs = "Topilgan qo‘shiqlar:\n\n"
        for idx, track in enumerate(result['tracks']['items'], start=1):
            songs += f"{idx}. {track['name']} - {track['artists'][0]['name']}\nLink: {track['external_urls']['spotify']}\n\n"
        update.message.reply_text(songs)
    else:
        update.message.reply_text("Afsus, bu qo‘shiq topilmadi.")


# Asosiy bot funksiyasi
def main() -> None:
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    # Komanda va xabarlar uchun handlerlar
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, identify_song_from_video))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, search_song_by_name))
    dispatcher.add_handler(CommandHandler("menu", menu_handler))

    # Botni ishga tushirish
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
