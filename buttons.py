import requests
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder



menu = InlineKeyboardMarkup(
  inline_keyboard=[
    [InlineKeyboardButton(text="Products 🛍", callback_data="shop"), InlineKeyboardButton(text="Website 🌐",web_app=WebAppInfo(url="https://uzum.uz/uz"))],
    [InlineKeyboardButton(text="Cart 🛒", callback_data="savat"), InlineKeyboardButton(text="Admin 👤", url="t.me/augustdk")]
  ]
)

url = requests.get("https://dummyjson.com/products")
response = url.json()
# print(len(response["products"]))

maxsulotlar = InlineKeyboardBuilder()
for i in response["products"]:
  maxsulotlar.button(text=i['title'], callback_data=i['title'])
maxsulotlar.add(InlineKeyboardButton(text="back", callback_data="menyu"))
maxsulotlar.adjust(3)


builder = InlineKeyboardBuilder()

# for index in range(1, 11):
#     builder.button(text=f"Set {index}", callback_data=f"set:{index}")
# builder.add(InlineKeyboardButton(text="ortga", callback_data="ortga"))
# builder.adjust(3, 2)

builder.button(text="add to cart", callback_data="add")

builder.add(InlineKeyboardButton(text="back", callback_data="ortga"))

builder.button(text="menu", callback_data="menyu")

builder.adjust(2, 2)

cart = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="cart", callback_data="savat"), InlineKeyboardButton(text="back", callback_data="shop")],
        [InlineKeyboardButton(text="menu", callback_data="menyu")]
    ]
)

after_cart = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Delete Products", callback_data="delete"), InlineKeyboardButton(text="menu", callback_data="menyu")]
    ]
)
