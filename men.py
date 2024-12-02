import subprocess
import os
import json
import logging
import requests
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from datetime import datetime

# URL JSON produk dari GitHub
PRODUK_JSON_URL = "https://raw.githubusercontent.com/zxsghcc/ncxxxg/refs/heads/main/produk.json"

# Konfigurasi API dan produk
config = {
    "api_username": "nGiUogmLMU",
    "api_key": "6dYGDRXYgDMJZ4gu6KXcPsdmyGHFC44R",
    "command": "beli-produk",
    "url": "https://www.simalakama.my.id/api/beli-produk",
    "produk_code": "",
    "msisdn": "",
    "payment_method": ""
}

# Logging setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram bot token
TOKEN = "BOT_TOKEN_ANDA"

# Fungsi untuk mengambil data produk dari URL
# Tambahkan fungsi load produk sebelum definisi fungsi view_products
def load_product_data():
    try:
        response = requests.get(PRODUK_JSON_URL)
        response.raise_for_status()
        return response.json()['data']
    except Exception as e:
        logger.error(f"Error loading product data: {e}")
        return []

# Pisahkan produk berdasarkan kategori
def organize_products_by_category(products):
    kategorized_products = {}
    for product in products:
        if product['status'] == 'aktif':
            kategori = product['kategori']
            if kategori not in kategorized_products:
                kategorized_products[kategori] = []
            kategorized_products[kategori].append(product)
    return kategorized_products

# Dashboard awal dengan deteksi username
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Cek apakah ini dari callback query atau command
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user = query.from_user
    elif update.message:
        user = update.effective_user
    else:
        logger.error("Unable to determine user in start handler")
        return

    current_date = datetime.now().strftime("%d %B %Y")
    
    welcome_message = (
        f"👋 Selamat datang, {user.first_name or 'Pengguna'}!\n"
        f"📅 Tanggal: {current_date}\n"
        f"🤴 Owner: t.me/zixxi990\n\n"
        "Silahkan Pilih Opsi:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔢 Masukkan Nomor HP", callback_data="enter_msisdn")],
        [InlineKeyboardButton("🛒 Lihat Produk", callback_data="view_categories")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Pilih metode reply berdasarkan jenis input
    try:
        if update.callback_query:
            await query.edit_message_text(welcome_message, reply_markup=reply_markup)
        elif update.message:
            await update.message.reply_text(welcome_message, reply_markup=reply_markup)
        else:
            logger.error("No valid update method found")
    except Exception as e:
        logger.error(f"Error in start handler: {e}")

async def view_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Cek apakah ini dari callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    
    # Ambil data produk dari API atau database
    try:
        # Ganti dengan metode pengambilan data sesuai sistem Anda
        response = requests.get(PRODUK_JSON_URL)
        
        if response.status_code == 200:
            product_data = response.json().get('data', [])
        else:
            product_data = []
        
        if not product_data:
            error_message = "Tidak ada kategori produk yang tersedia saat ini."
            if update.callback_query:
                await query.edit_message_text(error_message)
            else:
                await update.effective_message.reply_text(error_message)
            return

        # Ambil kategori unik
        categories = set(product.get('kategori', '') for product in product_data if product.get('status') == 'aktif')
        
        # Buat keyboard dengan kategori
        keyboard = []
        for category in categories:
            if category:  # Hindari kategori kosong
                button = [InlineKeyboardButton(
                    category, 
                    callback_data=f"category:{category}"
                )]
                keyboard.append(button)
        
        # Tambahkan tombol kembali
        keyboard.append([
            InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="start")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Pilih metode reply
        message_text = "📋 Pilih Kategori Produk:"
        
        if update.callback_query:
            await query.edit_message_text(
                message_text, 
                reply_markup=reply_markup
            )
        else:
            await update.effective_message.reply_text(
                message_text, 
                reply_markup=reply_markup
            )
    
    except requests.RequestException as req_err:
        error_message = f"Gagal mengambil kategori: {str(req_err)}"
        logger.error(error_message)
        
        if update.callback_query:
            await query.edit_message_text(error_message)
        else:
            await update.effective_message.reply_text(error_message)
    
    except Exception as e:
        error_message = f"Terjadi kesalahan: {str(e)}"
        logger.error(error_message)
        
        if update.callback_query:
            await query.edit_message_text(error_message)
        else:
            await update.effective_message.reply_text(error_message)

# Handler untuk menampilkan produk dalam kategori
async def show_category_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    kategori = query.data.split(':')[1]
    product_data = load_product_data()
    kategorized_products = organize_products_by_category(product_data)

    keyboard = []
    for product in kategorized_products.get(kategori, []):
        button_text = f"{product['nama_produk']} - Rp{product['harga_bayar']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"product:{product['produk_code']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Kembali ke Kategori", callback_data="view_categories")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Produk Kategori {kategori}:", reply_markup=reply_markup)

# Step 5: Show product details and allow purchase
# Tambahkan fungsi-fungsi baru

# Fungsi untuk kembali ke pilihan produk
async def back_to_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await view_products(update, context)

# Fungsi untuk mereset/ganti nomor telepon
async def reset_msisdn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    # Reset konfigurasi
    config["msisdn"] = ""
    config["produk_code"] = ""
    config["payment_method"] = ""
    
    # Kembali ke langkah awal
    keyboard = [[InlineKeyboardButton("Enter Phone Number", callback_data="enter_msisdn")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Please enter your phone number (MSISDN) to continue.", reply_markup=reply_markup)

# Fungsi untuk menambahkan tombol navigasi
def add_navigation_buttons(buttons):
    # Tambahkan tombol navigasi
    navigation_buttons = [
        [InlineKeyboardButton("🔙 Back to Products", callback_data="view_products")],
        [InlineKeyboardButton("🔄 Change Phone Number", callback_data="reset_msisdn")]
    ]
    return buttons + navigation_buttons

# Modifikasi fungsi view_products
async def view_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Cek apakah ini dari callback query atau direct call
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    
    # Pastikan nomor telepon sudah diset
    if not config["msisdn"]:
        await update.effective_message.reply_text("Silakan masukkan nomor HP terlebih dahulu.")
        return

    # Muat ulang data produk
    product_data = load_product_data()

    # Cek apakah ada kategori di callback data
    if update.callback_query and ':' in update.callback_query.data:
        try:
            category = update.callback_query.data.split(':')[1]
            filtered_products = [p for p in product_data if p['kategori'] == category]
        except IndexError:
            filtered_products = product_data
    else:
        filtered_products = product_data

    keyboard = []
    for product in filtered_products:
        if product['status'] == 'aktif':
            button_text = f"{product['nama_produk']} - {product['kategori']}"
            callback_data = f"product:{product['produk_code']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    # Tambahkan tombol navigasi
    navigation_buttons = [
        [InlineKeyboardButton("🔄 Ganti Nomor HP", callback_data="reset_msisdn")]
    ]
    keyboard.extend(navigation_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Pilih metode reply berdasarkan jenis input
    if update.callback_query:
        await query.edit_message_text("Pilih Produk:", reply_markup=reply_markup)
    else:
        await update.effective_message.reply_text("Pilih Produk:", reply_markup=reply_markup)

# Modifikasi fungsi product_details
async def product_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Muat ulang data produk
    product_data = load_product_data()

    product_code = query.data.split(':')[1]
    product = next((p for p in product_data if p['produk_code'] == product_code), None)

    if product:
        details = (
            f"Produk: {product['nama_produk']}\n"
            f"Kategori: {product['kategori']}\n"
            f"Kode: {product['produk_code']}\n"
            f"Harga Panel: {product['harga_panel']}\n"
            f"Harga Bayar: {product['harga_bayar']}\n"
            f"Deskripsi: {product['deskripsi']}\n"
            f"Status: {product['status']}"
        )
        # Show payment methods after product details
        keyboard = [
            [InlineKeyboardButton("Pulsa", callback_data=f"pay:BALANCE:{product_code}")],
            [InlineKeyboardButton("DANA", callback_data=f"pay:DANA:{product_code}")],
            [InlineKeyboardButton("GOPAY", callback_data=f"pay:GOPAY:{product_code}")],
            # Tambahkan tombol navigasi
            [InlineKeyboardButton("🔙 Kembali ke Produk", callback_data="view_categories")],
            [InlineKeyboardButton("🔄 Ganti Nomor HP", callback_data="reset_msisdn")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(details, reply_markup=reply_markup)
    else:
        await query.edit_message_text("Produk tidak ditemukan.")

# Step 6: Handle payment method selection
async def handle_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Muat ulang data produk
    product_data = load_product_data()  # Pastikan Anda memiliki fungsi ini

    payment_data = query.data.split(':')
    payment_method = payment_data[1]
    product_code = payment_data[2]

    # Cari detail produk
    product = next((p for p in product_data if p['produk_code'] == product_code), None)

    if not product:
        await query.edit_message_text("Produk tidak ditemukan.")
        return

    if not config.get("msisdn"):
        await query.edit_message_text("Silakan masukkan nomor HP terlebih dahulu.")
        return

    # Konfirmasi pembayaran
    keyboard = [
        [InlineKeyboardButton("✅ Konfirmasi", callback_data=f"confirm_payment:{payment_method}:{product_code}")],
        [InlineKeyboardButton("❌ Batal", callback_data="view_categories")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    konfirmasi_text = (
        f"Konfirmasi Pembayaran:\n"
        f"Produk: {product['nama_produk']}\n"
        f"Metode Pembayaran: {payment_method}\n"
        f"Harga: {product['harga_bayar']}\n"
        f"Nomor HP: {config['msisdn']}"
    )

    await query.edit_message_text(konfirmasi_text, reply_markup=reply_markup)

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    payment_data = query.data.split(':')
    payment_method = payment_data[1]
    product_code = payment_data[2]

    # Set konfigurasi
    config["produk_code"] = product_code
    config["payment_method"] = payment_method

    # Lanjutkan proses pembelian
    await buy_product(update, context)

# Step 7: Execute purchase
# Fungsi untuk memformat hasil pembelian dengan lebih rapi
def format_purchase_result(result_data, payment_method):
    formatted_message = "📋 Hasil Pembelian:\n\n"
    
    if result_data.get('success', False):
        data = result_data.get('data', {})
        formatted_details = [
            f"✅ Status: Berhasil Dibeli",
            f"🏷️ Produk: {data.get('produk', 'N/A')}",
            f"💰 Harga: {data.get('harga', 'N/A')}",
            f"🆔 ID Transaksi: {data.get('trx_id', 'N/A')}",
            f"💳 Metode Pembayaran: {data.get('metode_pembayaran', payment_method.upper())}",
            f"💵 Saldo Terakhir: {data.get('saldo_terakhir', 'N/A')}",
            f"🌟 Poin Didapat: {data.get('points', 0)}"
        ]
        
        # Tambahan untuk metode pembayaran spesifik
        if payment_method in ['DANA', 'GOPAY']:
            if data.get('link_pembayaran'):
                formatted_details.append(f"🔗 Link Pembayaran {payment_method.upper()}: {data.get('link_pembayaran')}")
                formatted_details.append("Silakan selesaikan pembayaran di aplikasi.")
        
        if data.get('catatan'):
            formatted_details.append(f"📝 Catatan: {data.get('catatan')}")
        
        formatted_message += "\n".join(formatted_details)
    else:
        # Pesan error yang lebih informatif
        formatted_message += f"❌ Pembelian Gagal\n"
        formatted_message += f"Pesan Error: {result_data.get('message', 'Kesalahan tidak diketahui')}"
    
    return formatted_message

# Modifikasi fungsi buy_product untuk menggunakan format yang baru
async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    try:
        product_code = config["produk_code"]
        msisdn = config["msisdn"]
        payment_method = config["payment_method"]

        # Tambahkan logging untuk debug
        logger.info(f"Memulai pembelian produk: {product_code}")
        logger.info(f"MSISDN: {msisdn}")
        logger.info(f"Metode Pembayaran: {payment_method}")

        php_code = f"""
<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

function encrypt_data($data, $apiKey) {{
    try {{
        $key = hash('sha256', $apiKey);
        $iv = openssl_random_pseudo_bytes(openssl_cipher_iv_length('aes-256-cbc'));
        $encrypted = openssl_encrypt($data, 'aes-256-cbc', $key, 0, $iv);
        return base64_encode($encrypted . '::' . $iv);
    }} catch (Exception $e) {{
        echo json_encode(['status' => false, 'error' => 'Encryption failed: ' . $e->getMessage()]);
        exit;
    }}
}}

// Log semua informasi untuk debugging
$debug_info = [
    'api_username' => "{config['api_username']}",
    'api_key' => "{config['api_key']}",
    'command' => "{config['command']}",
    'produk_code' => "{product_code}",
    'msisdn' => "{msisdn}",
    'payment_method' => "{payment_method}"
];

try {{
    $api_username = $debug_info['api_username'];
    $api_key = $debug_info['api_key'];
    $command = $debug_info['command'];
    $produk_code = $debug_info['produk_code'];
    $msisdn = $debug_info['msisdn'];
    $payment_method = $debug_info['payment_method'];

    $signature = md5($api_username . $api_key . $command);

    $data = json_encode([
        'api_username' => $api_username,
        'api_key' => $api_key,
        'produk_code' => $produk_code,
        'msisdn' => $msisdn,
        'pay' => $payment_method,
        'signature' => $signature
    ]);

    $xdata = encrypt_data($data, $api_key);

    $xtime = time();

    $url = "{config['url']}";

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        "Content-Type: application/json",
        "username: $api_username",
        "xdata: $xdata",
        "xtime: $xtime"
    ]);

    $response = curl_exec($ch);
    
    // Tambahkan error checking
    if ($response === false) {{
        $curl_error = curl_error($ch);
        echo json_encode([
            'status' => false, 
            'error' => 'cURL Error: ' . $curl_error,
            'debug_info' => $debug_info
        ]);
        exit;
    }}

    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    // Log raw response untuk debugging
    $raw_response = $response;

    $responseData = json_decode($response, true);

    if (json_last_error() === JSON_ERROR_NONE) {{
        // Tambahkan informasi debug ke response
        $responseData['debug'] = [
            'http_code' => $http_code,
            'raw_response' => $raw_response,
            'debug_info' => $debug_info
        ];
        echo json_encode($responseData, JSON_PRETTY_PRINT);
    }} else {{
        echo json_encode([
            'status' => false, 
            'error' => 'Invalid JSON Response', 
            'raw_response' => $raw_response,
            'debug_info' => $debug_info
        ], JSON_PRETTY_PRINT);
    }}
}} catch (Exception $e) {{
    echo json_encode([
        'status' => false, 
        'error' => 'Unexpected error: ' . $e->getMessage(),
        'debug_info' => $debug_info
    ]);
}}
?>
"""
        # Tulis PHP code ke file
        php_file = './temp_script.php'
        with open(php_file, 'w') as file:
            file.write(php_code)

        try:
            # Jalankan PHP script
            result = subprocess.run(['php', php_file], capture_output=True, text=True, check=True)
            output = result.stdout.strip()

            # Log raw output untuk debugging
            logger.info(f"Raw PHP Output: {output}")

            try:
                # Parse JSON response
                json_data = json.loads(output)
                
                # Log parsed JSON untuk debugging
                logger.info(f"Parsed JSON: {json.dumps(json_data, indent=2)}")
                
                # Format hasil dengan pesan yang rapi
                formatted_result = format_purchase_result(json_data, payment_method)
                
                # Tambahkan tombol navigasi
                keyboard = [
                    [InlineKeyboardButton("🔙 Kembali ke Produk", callback_data="view_categories")],
                    [InlineKeyboardButton("🔄 Ganti Nomor", callback_data="reset_msisdn")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Kirim pesan dengan hasil yang diformat dan tombol navigasi
                await query.edit_message_text(
                    formatted_result, 
                    reply_markup=reply_markup
                )
            
            except json.JSONDecodeError as e:
                # Log detail error parsing JSON
                logger.error(f"JSON Decode Error: {e}")
                logger.error(f"Problematic output: {output}")
                
                await query.edit_message_text(f"Error parsing response: {str(e)}")
            
            finally:
                # Hapus temporary PHP file
                if os.path.exists(php_file):
                    os.remove(php_file)

        except subprocess.CalledProcessError as e:
            # Log detail error subprocess
            logger.error(f"Subprocess error: {e}")
            logger.error(f"Subprocess stdout: {e.stdout}")
            logger.error(f"Subprocess stderr: {e.stderr}")
            
            await query.edit_message_text(f"Subprocess error: {str(e)}")

    except Exception as e:
        # Log error umum
        logger.error(f"Unexpected error in buy_product: {e}", exc_info=True)
        
        await query.edit_message_text(f"An unexpected error occurred: {str(e)}")

# Step 2: Prompt for Phone Number (MSISDN)
async def enter_msisdn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    # Ask the user to enter their MSISDN
    keyboard = [
        [InlineKeyboardButton("🏠 Kembali ke Awal", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Silakan masukkan nomor HP Anda dalam format 62xxxxxxxxxxx:", 
        reply_markup=reply_markup
    )

    # We will wait for the user to reply with their phone number
    return

# Step 3: Set MSISDN after receiving input
async def handle_msisdn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msisdn = update.message.text.strip()
    
    if msisdn.startswith('62'):
        config["msisdn"] = msisdn
        
        # Tampilkan konfirmasi dan pilihan selanjutnya
        keyboard = [
            [InlineKeyboardButton("🛒 Lihat Produk", callback_data="view_categories")],
            [InlineKeyboardButton("🏠 Kembali ke Awal", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Nomor HP {msisdn} tersimpan. Silakan pilih opsi:", 
            reply_markup=reply_markup
        )
    else:
        keyboard = [
            [InlineKeyboardButton("🔢 Coba Lagi", callback_data="enter_msisdn")],
            [InlineKeyboardButton("🏠 Kembali ke Awal", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Format nomor HP tidak valid. Gunakan format 62xxxxxxxxxxx.", 
            reply_markup=reply_markup
        )

# Modifikasi fungsi main untuk menambahkan handler baru
def main() -> None:
    application = Application.builder().token(TOKEN).build()
    
    # Handler untuk berbagai cara memulai bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(start, pattern="^start$"))
    
    # Handler lainnya
    application.add_handler(CallbackQueryHandler(view_categories, pattern="^view_categories$"))
    application.add_handler(CallbackQueryHandler(enter_msisdn, pattern="^enter_msisdn$"))
    application.add_handler(CallbackQueryHandler(show_category_products, pattern="^category:"))
    
    # Handler lama
    application.add_handler(CallbackQueryHandler(view_products, pattern="^category:"))
    application.add_handler(CallbackQueryHandler(product_details, pattern="^product:"))
    application.add_handler(CallbackQueryHandler(handle_payment_method, pattern="^pay:"))
    
    # Handler konfirmasi pembayaran
    application.add_handler(CallbackQueryHandler(confirm_payment, pattern="^confirm_payment:"))
    
    # Handler navigasi
    application.add_handler(CallbackQueryHandler(back_to_products, pattern="^view_products$"))
    application.add_handler(CallbackQueryHandler(reset_msisdn, pattern="^reset_msisdn$"))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msisdn))
    application.run_polling()

if __name__ == "__main__":
    main()
