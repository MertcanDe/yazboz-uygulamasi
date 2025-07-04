from flask import Flask, render_template, request, redirect, url_for, session

# Flask uygulamasını oluştur
app = Flask(__name__)
# Session (oturum) verilerini güvenli bir şekilde saklamak için gizli bir anahtar gerekli
app.secret_key = 'okey-yazboz-cok-gizli-anahtar'

# Okey renklerinin katsayıları
OKEY_KATSAYILARI = {
    "sarı": 3, "mavi": 6, "kırmızı": 4, "siyah": 5
}


@app.route('/')
def index():
    """Ana sayfa. Oyuncu isimleri girilmediyse kurulumu, girildiyse oyun ekranını gösterir."""
    # Eğer session'da oyuncu bilgisi yoksa, başlangıç ekranını göster
    if 'players' not in session:
        return render_template('index.html', setup_mode=True)

    # Oyun bittiyse, sonuç ekranını göster
    game_over = session.get('current_hand', 1) > 11

    # Oyuncu bilgisi varsa, oyun ekranını render et
    return render_template('index.html',
                           setup_mode=False,
                           game_data=session,
                           game_over=game_over)


@app.route('/start_game', methods=['POST'])
def start_game():
    """Oyuncu isimlerini alır, session'ı başlatır ve oyunu başlatır."""
    players = [
        request.form['player1'],  # Üst (Ayşe)
        request.form['player2'],  # Sağ (Mehmet)
        request.form['player3'],  # Alt (Ahmet)
        request.form['player4']  # Sol (Fatma)
    ]

    if any(name == "" for name in players):
        # Eğer bir isim boşsa, hata mesajı ile ana sayfaya yönlendir
        return redirect(url_for('index'))

    # Session'da oyun verilerini sakla
    session['players'] = players
    session['team1_name'] = f"{players[2]}-{players[0]}"  # Ahmet-Ayşe
    session['team2_name'] = f"{players[3]}-{players[1]}"  # Fatma-Mehmet
    session['scores'] = {session['team1_name']: 0, session['team2_name']: 0}
    session['current_hand'] = 1
    session['results'] = []

    return redirect(url_for('index'))


@app.route('/save_hand', methods=['POST'])
def save_hand():
    """Her elin sonucunu kaydeden fonksiyon."""
    if 'current_hand' not in session or session['current_hand'] > 11:
        return redirect(url_for('index'))

    # Formdan gelen verileri al
    okey_color = request.form['okey_color']
    winner_team = request.form['winner_team']
    penalty_points = int(request.form['penalty_points'])

    # Ceza puanını hesapla
    katsayi = OKEY_KATSAYILARI[okey_color]
    ceza = katsayi * penalty_points

    # Skoru güncelle
    losing_team = session['team2_name'] if winner_team == session['team1_name'] else session['team1_name']
    session['scores'][losing_team] += ceza

    # Sonucu listeye ekle
    hand_result = {
        "el": session['current_hand'],
        "okey": okey_color,
        "kazanan": winner_team.split('-')[0],  # Sadece ilk oyuncunun adını al
        "sayilar": penalty_points,
        "ceza": ceza
    }
    session['results'].append(hand_result)

    # Sonraki ele geç
    session['current_hand'] += 1

    # Flask session'ı manuel olarak güncellendi olarak işaretle
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