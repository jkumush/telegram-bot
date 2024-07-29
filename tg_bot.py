import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from config1 import BOT_TOKEN as token
from button import menu, maxsulotlar, builder, cart, after_cart
import requests
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sqlite3
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


logging.basicConfig(level=logging.INFO)
bot = Bot(token=token)
dp = Dispatcher()



def create_connection():
    conn = sqlite3.connect('shop.db')
    return conn

def init_db():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_products
                      (user_id INTEGER, product_name TEXT, photo TEXT, price INTEGER, description TEXT, quantity INTEGER)''')
    conn.commit()  
    conn.close()

def add_product(user_id, product_name, photo, price, description, quantity):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantity FROM user_products WHERE user_id=? AND product_name=?", (user_id, product_name))
    result = cursor.fetchone()
    if result:
        curr_quantity = result[0]
        new_quantity = curr_quantity + quantity
        cursor.execute("UPDATE user_products SET quantity=? WHERE user_id=? AND product_name=?", (new_quantity, user_id, product_name))
    else:
        cursor.execute("INSERT INTO user_products (user_id, product_name, photo, price, description, quantity) VALUES (?, ?, ?, ?, ?, ?)", (user_id, product_name, photo, price, description, quantity))
    conn.commit()

def get_products(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, photo, price, description, quantity FROM user_products WHERE user_id=?", (user_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def delete_product(user_id, product_name, quantity):
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT quantity FROM user_products WHERE user_id=? AND product_name=?", (user_id, product_name))
    result = cursor.fetchone()
    if result:
        curr_quantity = result[0]
        new_quantity = curr_quantity - int(quantity)
        
        if new_quantity > 0:
            cursor.execute("UPDATE user_products SET quantity=? WHERE user_id=? AND product_name=?", (new_quantity, user_id, product_name))
        else:
            cursor.execute("DELETE FROM user_products WHERE user_id=? AND product_name=?", (user_id, product_name))
        
        
        conn.commit()
    conn.close()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.update_data(navigation_history="menu")
    await message.answer_photo(photo="https://www.kaspersky.com/content/en-global/images/repository/isc/2021/safe_shopping_1.jpg", caption="Welcome to our shop", reply_markup=menu)

@dp.callback_query(F.data == "menyu")
async def Menyu(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(navigation_history="menu")
    await call.message.answer_photo(photo="https://www.spot.uz/media/img/2022/08/85brvW16603795118030_b.jpg", reply_markup=menu)
    await call.message.delete()

@dp.callback_query(F.data == 'shop')
async def Shopping(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(navigation_history="shop")
    await call.message.answer_photo(photo="https://www.spot.uz/media/img/2022/08/85brvW16603795118030_b.jpg", caption="Choose one product", reply_markup=maxsulotlar.as_markup())
    await call.message.delete()


class Cart(StatesGroup):
    quantity = State()
    product_title = State()
    price = State()
    photo = State()
    description = State()
    delete_quantity = State()
    navigation_history = State()
    

@dp.callback_query(F.data == "add")
async def Savat(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Enter the amonut of product in numbers")
    await state.set_state(Cart.quantity)

# dp.callback_query(F.data == "add")
# async def Savat(call: types.CallbackQuery, state: FSMContext):
#     await call.message.answer("Mahsulot sonini kiriting:")
#     await state.set_state(Cart.quantity)

@dp.message(Cart.quantity)
async def Savat_qoshish(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(quantity=message.text)
        user_data = await state.get_data()
        user_id = message.from_user.id
        product_name = user_data["product_title"]
        quantity = user_data["quantity"]
        price = user_data["price"]
        photo = user_data["photo"]
        description = user_data["description"]
        add_product(user_id, product_name,photo, price, description, int(quantity))
        await state.clear()
        await message.answer("Product added to the cart", reply_markup=cart)
    else:
        await message.answer("Enter a number")
        await state.set_state(Cart.quantity)
    

@dp.callback_query(F.data == "savat")
async def Savat(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(navigation_history="cart")
    user_id = call.from_user.id
    products = get_products(user_id)
    if not products:
        await call.message.answer("Your cart is empty", reply_markup=menu)
        # await call.message.answer("Your cart is empty")
        # await state.update_data(navigation_history="menyu")
    else:
        for name, photo_url, price, description, quantity in products:
            caption = f"{name}\nPrice: {price}\n{description} \nQuantity: {quantity}"
            await call.message.answer_photo(photo=photo_url, caption=caption)
            
        all_price = sum([price * quantity for name, photo_url, price, description, quantity in products])
        await call.message.answer(f"Total price: {all_price:.2f}$", reply_markup=after_cart)
        
    
@dp.callback_query(F.data == "delete")
async def Delete(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(navigation_history="delete")
    user_id = call.from_user.id
    products = get_products(user_id)
    
    delete_markup = InlineKeyboardBuilder()
    for product in products:
        delete_markup.button(text=product[0], callback_data=f"delete:{product[0]}")
    delete_markup.add(InlineKeyboardButton(text="Delete All", callback_data="clear"))
    delete_markup.add(InlineKeyboardButton(text="menu", callback_data="menyu"))
    delete_markup.adjust(2)
    
    await call.message.answer("Select a product to delete", reply_markup=delete_markup.as_markup())
    await state.set_state("delete_product")

@dp.callback_query(F.data.startswith("delete"))
async def Delete_product(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    product_name = call.data.split(":")[1]
    products = get_products(user_id)
    
    for name, photo_url, price, description, quantity in products:
        if name == product_name:
            caption = f"{name}\nPrice: {price}\n{description} \nQuantity: {quantity}"
            await call.message.answer_photo(photo=photo_url, caption=caption)
            break
        
    await state.update_data(product_name=product_name)
    await call.message.answer(f"Quantity to delete:")
    await state.set_state(Cart.delete_quantity)


@dp.message(Cart.delete_quantity)
async def Delete_quantity(message: types.Message, state: FSMContext):
    quantity = message.text
    user_id = message.from_user.id
    user_data = await state.get_data()
    product_name = user_data["product_name"]
    
    delete_product(user_id, product_name, quantity)
    await message.answer("Product deleted", reply_markup=after_cart)
    await state.clear()
    
@dp.callback_query(F.data == "clear")
async def Clear(call: types.CallbackQuery):
    user_id = call.from_user.id
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_products WHERE user_id =?", (user_id,))
    conn.commit()
    conn.close()
    await call.message.answer("All products are deleted", reply_markup=menu)
    
@dp.callback_query(F.data == "ortga") 
async def Orqaga(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    navigation_history = user_data.get("navigation_history")
    if navigation_history == "menu":
        await cmd_start(call.message, state)
    elif navigation_history == "shop":
        await Shopping(call, state)
    elif navigation_history == "cart":
        await Savat(call, state)
    elif navigation_history == "delete":
        await Delete(call, state)
    await call.message.delete()

@dp.callback_query(F.data)
async def Xarid(call: types.CallbackQuery, state: FSMContext):
  maxx = call.data
  url = requests.get("https://dummyjson.com/products")
  response = url.json()
  for i in response['products']:
     if maxx == i["title"]:
        await state.update_data(product_title=i["title"])
        await state.update_data(price=i["price"])
        await state.update_data(photo=i["images"][0])
        await state.update_data(description=i["description"])
        await call.message.answer_photo(photo=i['images'][0], caption=f"About: {i['description']}\nPrice: {i['price']} $", reply_markup=builder.as_markup())

    
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
      asyncio.run(main())
    except:
        print("the end")
