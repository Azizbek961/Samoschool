import pygame
import heapq
import os

# Pygame ishga tushirish
pygame.init()

# Ekran o'lchamlari
EKRAN_KENGLIK = 1200
EKRAN_BALANDLIK = 700
KATAK_HAJMI = 50  # Har bir katak 50x50 piksel

# Ranglar
OQQUV = (255, 255, 255)
QORA = (0, 0, 0)
QIZIL = (255, 0, 0)
YASHILKO = (0, 255, 0)
SARIQ = (255, 255, 0)
QIZILKO = (255, 100, 100)

# Xarita turlari
TUPROQ = 0
KOL = 1
TOSH = 2
DARAXT = 3
MAYSA = 4


# Rasmlarni yuklash
def rasmlarni_yuklash():
    """Rasmlarni yuklaydi"""
    rasmlar = {}
    rasm_dir = 'rasmlar'

    if not os.path.exists(rasm_dir):
        print(f"❌ {rasm_dir} katalogi topilmadi!")
        return rasmlar

    rasm_nomlari = {
        'tuproq': 'tuproq.png',
        'kol': 'kol.png',
        'tosh': 'tosh.png',
        'daraxt': 'daraxt.png',
        'maysa': 'maysa.png',
        'avatar': 'avatar.png'
    }

    for adi, fayl in rasm_nomlari.items():
        path = os.path.join(rasm_dir, fayl)
        try:
            rasm = pygame.image.load(path)
            rasm = pygame.transform.scale(rasm, (KATAK_HAJMI, KATAK_HAJMI))
            rasmlar[adi] = rasm
            print(f"✅ {adi}: {fayl} yuklandi")
        except Exception as e:
            print(f"❌ {adi}: {fayl} yuklash xatosi - {e}")

    return rasmlar


# Xarita yaratish
def xarita_yaratish():
    """Tasodifiy xarita yaratadi"""
    kenglik = EKRAN_KENGLIK // KATAK_HAJMI
    balandlik = EKRAN_BALANDLIK // KATAK_HAJMI
    xarita = []

    for y in range(balandlik):
        qator = []
        for x in range(kenglik):
            # Tuproq - default
            katak = TUPROQ

            # Ko'l - random
            if (x + y) % 8 == 0 and x > 3 and y > 3 and x < kenglik - 3:
                katak = KOL

            # Tosh - random
            if (x * 3 + y) % 11 == 0 and x > 4 and y > 4 and x < kenglik - 4:
                katak = TOSH

            # Daraxt - random
            if (x * 2 + y * 3) % 13 == 0 and x > 2 and y > 2 and x < kenglik - 2:
                katak = DARAXT

            # Maysa - random
            if (x + y * 2) % 9 == 0 and x > 3 and y > 3 and x < kenglik - 3:
                katak = MAYSA

            qator.append(katak)
        xarita.append(qator)

    return xarita


# A* algoritmi - yo'l topish
def yo_l_top(xarita, boshlang_i, manzil):
    """A* algoritmi bilan yo'l topadi"""
    kenglik = len(xarita[0])
    balandlik = len(xarita)

    def manhattan(a, b):
        """Manhattan masofa"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def qo_shni_borish_mumkin(x, y):
        """Katak bosa oladimi"""
        if x < 0 or x >= kenglik or y < 0 or y >= balandlik:
            return False
        katak = xarita[y][x]
        # Faqat tuproq va maysa bosa olamiz
        return katak in [TUPROQ, MAYSA]

    # Bosh qiymatlar
    open_set = [(0, boshlang_i)]
    came_from = {}
    g_score = {boshlang_i: 0}
    f_score = {boshlang_i: manhattan(boshlang_i, manzil)}
    closed_set = set()

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == manzil:
            # Yo'lni qayta tuzish
            yo_l = []
            while current in came_from:
                yo_l.append(current)
                current = came_from[current]
            yo_l.append(boshlang_i)
            return yo_l[::-1]

        if current in closed_set:
            continue

        closed_set.add(current)
        x, y = current

        # 4 tomonga ko'rish (yuqori, pastki, chap, o'ng)
        qo_shnilar = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

        for qo_shni in qo_shnilar:
            nx, ny = qo_shni

            if not qo_shni_borish_mumkin(nx, ny) or qo_shni in closed_set:
                continue

            tentative_g = g_score[current] + 1

            if qo_shni not in g_score or tentative_g < g_score[qo_shni]:
                came_from[qo_shni] = current
                g_score[qo_shni] = tentative_g
                f = tentative_g + manhattan(qo_shni, manzil)
                f_score[qo_shni] = f
                heapq.heappush(open_set, (f, qo_shni))

    return []  # Yo'l topilmadi


class Avatar:
    """Avatarni ifodalaydi"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.yo_l = []
        self.yo_l_indeksi = 0
        self.harakatlanmoqda = False

    def yo_lni_belgilash(self, yo_l):
        """Yo'l belgilash"""
        self.yo_l = yo_l
        self.yo_l_indeksi = 1  # Boshlang'ichdan boshlash
        self.harakatlanmoqda = True

    def yangilash(self):
        """Avatar harakatini yangilash"""
        if self.harakatlanmoqda and self.yo_l_indeksi < len(self.yo_l):
            self.x, self.y = self.yo_l[self.yo_l_indeksi]
            self.yo_l_indeksi += 1
        elif self.yo_l_indeksi >= len(self.yo_l):
            self.harakatlanmoqda = False

    def chizish(self, ekran, avatar_rasm):
        """Avatarni ekranga chizish"""
        if avatar_rasm:
            ekran.blit(avatar_rasm, (self.x * KATAK_HAJMI, self.y * KATAK_HAJMI))
        else:
            # Rasm bo'lmasa, sade aylana chiz
            x_piksel = self.x * KATAK_HAJMI + KATAK_HAJMI // 2
            y_piksel = self.y * KATAK_HAJMI + KATAK_HAJMI // 2
            pygame.draw.circle(ekran, SARIQ, (x_piksel, y_piksel), 15)


# Asosiy o'yin
def o_yin():
    ekran = pygame.display.set_mode((EKRAN_KENGLIK, EKRAN_BALANDLIK))
    pygame.display.set_caption("Avatar Pathfinding - A* Algoritmi")
    soat = pygame.time.Clock()

    # Rasmlarni yuklash
    rasmlar = rasmlarni_yuklash()

    # Xarita yaratish
    xarita = xarita_yaratish()

    # A nuqta va B nuqta
    A = (2, 2)
    B = (EKRAN_KENGLIK // KATAK_HAJMI - 3, EKRAN_BALANDLIK // KATAK_HAJMI - 3)

    # Avatar
    avatar = Avatar(A[0], A[1])

    print("🔍 Yo'l topilmoqda...")
    # Yo'l topish
    yo_l = yo_l_top(xarita, A, B)

    if yo_l:
        print(f"✅ Yo'l topildi! Uzunlik: {len(yo_l)} katak")
        avatar.yo_lni_belgilash(yo_l)
    else:
        print("❌ Yo'l topilmadi!")

    # Matn
    shrift_katta = pygame.font.Font(None, 36)
    shrift_kichik = pygame.font.Font(None, 24)

    ish_davom = True
    while ish_davom:
        for tadbir in pygame.event.get():
            if tadbir.type == pygame.QUIT:
                ish_davom = False
            elif tadbir.type == pygame.KEYDOWN:
                if tadbir.key == pygame.K_r:  # R tugmasi - qayta yo'l topish
                    yo_l = yo_l_top(xarita, A, B)
                    if yo_l:
                        avatar.yo_lni_belgilash(yo_l)
                        print("🔄 Yo'l qayta topildi!")

        # Ekranlarni rejalash
        ekran.fill(OQQUV)

        # Xaritani chizish
        for y in range(len(xarita)):
            for x in range(len(xarita[0])):
                katak_turi = xarita[y][x]

                if katak_turi == TUPROQ and 'tuproq' in rasmlar:
                    ekran.blit(rasmlar['tuproq'], (x * KATAK_HAJMI, y * KATAK_HAJMI))
                elif katak_turi == KOL and 'kol' in rasmlar:
                    ekran.blit(rasmlar['kol'], (x * KATAK_HAJMI, y * KATAK_HAJMI))
                elif katak_turi == TOSH and 'tosh' in rasmlar:
                    ekran.blit(rasmlar['tosh'], (x * KATAK_HAJMI, y * KATAK_HAJMI))
                elif katak_turi == DARAXT and 'daraxt' in rasmlar:
                    ekran.blit(rasmlar['daraxt'], (x * KATAK_HAJMI, y * KATAK_HAJMI))
                elif katak_turi == MAYSA and 'maysa' in rasmlar:
                    ekran.blit(rasmlar['maysa'], (x * KATAK_HAJMI, y * KATAK_HAJMI))

        # Yo'lni chizish (sariq chiziqlar)
        if avatar.yo_l and len(avatar.yo_l) > 1:
            for i in range(len(avatar.yo_l) - 1):
                x1 = avatar.yo_l[i][0] * KATAK_HAJMI + KATAK_HAJMI // 2
                y1 = avatar.yo_l[i][1] * KATAK_HAJMI + KATAK_HAJMI // 2
                x2 = avatar.yo_l[i + 1][0] * KATAK_HAJMI + KATAK_HAJMI // 2
                y2 = avatar.yo_l[i + 1][1] * KATAK_HAJMI + KATAK_HAJMI // 2
                pygame.draw.line(ekran, SARIQ, (x1, y1), (x2, y2), 3)

        # A va B nuqtalarni chizish
        A_x = A[0] * KATAK_HAJMI + KATAK_HAJMI // 2
        A_y = A[1] * KATAK_HAJMI + KATAK_HAJMI // 2
        pygame.draw.circle(ekran, QIZIL, (A_x, A_y), 15)
        pygame.draw.circle(ekran, QORA, (A_x, A_y), 15, 3)

        B_x = B[0] * KATAK_HAJMI + KATAK_HAJMI // 2
        B_y = B[1] * KATAK_HAJMI + KATAK_HAJMI // 2
        pygame.draw.circle(ekran, YASHILKO, (B_x, B_y), 15)
        pygame.draw.circle(ekran, QORA, (B_x, B_y), 15, 3)

        # Avatarni yangilash va chizish
        avatar.yangilash()
        avatar.chizish(ekran, rasmlar.get('avatar'))

        # Ma'lumot paneli
        panel_y = EKRAN_BALANDLIK - 130
        pygame.draw.rect(ekran, (220, 220, 220), (0, panel_y, EKRAN_KENGLIK, 130))
        pygame.draw.line(ekran, QORA, (0, panel_y), (EKRAN_KENGLIK, panel_y), 2)

        # Matn
        matn1 = shrift_katta.render("🔴 BOSHLASH  🟢 MANZIL  ➡️ YO'L", True, QORA)
        ekran.blit(matn1, (20, panel_y + 10))

        if avatar.harakatlanmoqda:
            matn2 = shrift_katta.render(f"▶️ Avatar harakatlanmoqda... {avatar.yo_l_indeksi}/{len(avatar.yo_l)}",
                                        True, (0, 150, 0))
        else:
            if avatar.yo_l:
                matn2 = shrift_katta.render("✅ Avatar manzilga yetdi!", True, YASHILKO)
            else:
                matn2 = shrift_katta.render("❌ Yo'l topilmadi!", True, QIZIL)

        ekran.blit(matn2, (20, panel_y + 50))

        matn3 = shrift_kichik.render("R tugmasi - qayta yo'l topish", True, (100, 100, 100))
        ekran.blit(matn3, (20, panel_y + 90))

        pygame.display.flip()
        soat.tick(1)  # 1 katak/sekund (sekin harakat)

    pygame.quit()


if __name__ == "__main__":
    print("🎮 Avatar Pathfinding O'yni Boshlandi!")
    print("=" * 50)
    o_yin()