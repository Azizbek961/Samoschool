import operator   # Pythonning 'operator' modulini chaqiramiz, arifmetik funksiyalarni olish uchun

# Operatorlarga mos funksiyalar lug‘ati
ops = {
    '+': operator.add,       # '+' belgisi uchun qo‘shish funksiyasi
    '-': operator.sub,       # '-' belgisi uchun ayirish funksiyasi
    '*': operator.mul,       # '*' belgisi uchun ko‘paytirish funksiyasi
    '/': operator.truediv,   # '/' belgisi uchun haqiqiy bo‘lish funksiyasi
    '^': operator.pow        # '^' belgisi uchun darajaga oshirish funksiyasi
}

# Kalkulyator funksiyasi: a op b
def calc(a, op, b):
    if op not in ops:                       # Agar kiritilgan operator lug‘atda bo‘lmasa
        raise ValueError("Ruxsat etilmagan operator.")  # Xatolik chiqaradi

    if op == '/' and b == 0:                # Bo‘lish va ikkinchi son 0 bo‘lsa
        raise ZeroDivisionError("0 ga bo'linmaydi.")    # 0 ga bo‘lish xatosi

    return ops[op](a, b)                    # Mos operator funksiyasini bajaradi: ops[op](a,b)

print("Xavfsiz kalkulator. Misol: 2 + 3")   # Boshlanish uchun foydalanuvchiga xabar

# Foydalanuvchi bilan doimiy ishlaydigan sikl
while True:
    yas = input("Format: son operator son (yoki 'exit'): ").strip()
    # foydalanuvchidan matn oladi; strip() → bo'sh joylarni olib tashlaydi

    if yas.lower() in ('exit', 'quit'):     # Agar foydalanuvchi 'exit' yoki 'quit' yozsa
        print("Xayr!")                      # xayrlashadi
        break                               # siklni to‘xtatadi

    try:
        parts = yas.split()                 # Kiritilgan matnni bo'sh joy bo‘yicha bo‘ladi
        if len(parts) != 3:                 # Uchta qism bo‘lmasa (masalan -> "2 + 3")
            raise ValueError("To'g'ri format: 2 + 3")

        a = float(parts[0])                 # 1-qism → birinchi son
        op = parts[1]                       # 2-qism → operator
        b = float(parts[2])                 # 3-qism → ikkinchi son

        print("=>", calc(a, op, b))         # Natijani chop etadi

    except Exception as e:                  # Agar yuqorida biror joyda xato bo‘lsa
        print("Xato:", e)                   # xato xabarini chiqaradi
