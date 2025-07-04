from flask import Flask, render_template, request, redirect, url_for, session

# Flask uygulamasını oluştur
app = Flask(__name__)
# Session (oturum) verilerini güvenli bir şekilde saklamak için gizli bir anahtar gerekli
app.secret_key = 'okey-yazboz-cok-gizli-anahtar'

# Okey renklerinin katsayıları ve hex renk kodları
OKEY_KATSAYILARI = {
    "sarı": {"katsayi": 3, "color": "#F1C40F"},
    "kırmızı": {"katsayi": 4, "color": "#E74C3C"},
    "siyah": {"katsayi": 5, "color": "#ecf0f1"},  # Koyu arka planda daha iyi okunması için beyaz/açık gri
    "mavi": {"katsayi": 6, "color": "#3498DB"}
}


@app.route('/')
def index():
    """
    Ana sayfa. Oyuncu isimleri girilmediyse kurulumu, girildiyse oyun ekranını gösterir.
    """
    # Eğer session'da oyuncu bilgisi yoksa, başlangıç ekranını göster
    if 'players' not in session:
        return render_template('index.html', setup_mode=True)

    # Okey renklerini HTML'de sıralı göstermek için katsayılarına göre sırala
    sorted_okey_data = sorted(OKEY_KATSAYILARI.items(), key=lambda item: item[1]['katsayi'])

    # Oyunun bitip bitmediğini kontrol et
    game_over = session.get('current_hand', 1) > 11

    # Oyuncu bilgisi varsa, oyun ekranını render et ve sıralı okey verisini gönder
    return render_template('index.html',
                           setup_mode=False,
                           game_data=session,
                           game_over=game_over,
                           okey_data_sorted=sorted_okey_data,
                           OKEY_KATSAYILARI=OKEY_KATSAYILARI)  # Skor tablosunda renklendirme için


@app.route('/start_game', methods=['POST'])
def start_game():
    """Oyuncu ve takım isimlerini alır, session'ı başlatır ve oyunu başlatır."""
    players = [
        request.form['player1'], request.form['player2'],
        request.form['player3'], request.form['player4']
    ]

    team1_name_from_form = request.form['team1_name']
    team2_name_from_form = request.form['team2_name']

    # Eğer bir isim boşsa, kurulum ekranına geri dön
    if any(name == "" for name in players):
        return redirect(url_for('index'))

    # Session'da oyun verilerini sakla
    session['team1_name'] = team1_name_from_form if team1_name_from_form else "Takım A"
    session['team2_name'] = team2_name_from_form if team2_name_from_form else "Takım B"

    session['players'] = players
    # Takımları ve oyuncularını bir sözlük yapısında sakla
    session['teams'] = {
        session['team1_name']: [players[2], players[0]],  # Alt ve Üst oyuncular
        session['team2_name']: [players[3], players[1]]  # Sol ve Sağ oyuncular
    }

    session['scores'] = {session['team1_name']: 0, session['team2_name']: 0}
    session['current_hand'] = 1
    session['results'] = []

    return redirect(url_for('index'))


@app.route('/save_hand', methods=['POST'])
def save_hand():
    """Her elin sonucunu kaydeden ve kazanan takımı otomatik bulan fonksiyon."""
    if 'current_hand' not in session or session['current_hand'] > 11:
        return redirect(url_for('index'))

    # Formdan gelen verileri al
    okey_color = request.form['okey_color']
    penalty_points = int(request.form['penalty_points'])
    winning_player = request.form['winning_player']

    # Kazanan oyuncuya göre kazanan takımı bul
    winner_team = None
    for team, players_in_team in session['teams'].items():
        if winning_player in players_in_team:
            winner_team = team
            break

    if not winner_team:
        return "Hata: Oyuncu bir takıma ait değil.", 400

    # Ceza puanını hesapla
    katsayi = OKEY_KATSAYILARI[okey_color]['katsayi']
    ceza = katsayi * penalty_points

    # Skoru güncelle
    losing_team = session['team2_name'] if winner_team == session['team1_name'] else session['team1_name']
    session['scores'][losing_team] += ceza

    # Sonucu listeye ekle
    hand_result = {
        "el": session['current_hand'],
        "okey": okey_color,
        "kazanan_takim": winner_team,
        "kazanan_oyuncu": winning_player,
        "sayilar": penalty_points,
        "ceza": ceza
    }
    session['results'].append(hand_result)

    # Sonraki ele geç
    session['current_hand'] += 1
    session.modified = True

    return redirect(url_for('index'))


@app.route('/reset')
def reset():
    """Oyunu sıfırlar ve başlangıç ekranına döner."""
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    # '0.0.0.0' adresi, uygulamanın ağdaki diğer cihazlar tarafından erişilebilir olmasını sağlar.
    app.run(host='0.0.0.0', port=5000, debug=True)
