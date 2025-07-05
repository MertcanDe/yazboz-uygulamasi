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
    if 'players' not in session:
        return render_template('index.html', setup_mode=True)

    sorted_okey_data = sorted(OKEY_KATSAYILARI.items(), key=lambda item: item[1]['katsayi'])
    game_over = session.get('current_hand', 1) > 11

    return render_template('index.html',
                           setup_mode=False,
                           game_data=session,
                           game_over=game_over,
                           okey_data_sorted=sorted_okey_data,
                           OKEY_KATSAYILARI=OKEY_KATSAYILARI)


@app.route('/start_game', methods=['POST'])
def start_game():
    """Oyuncu ve takım isimlerini alır, session'ı başlatır ve oyunu başlatır."""
    players = [
        request.form['player1'], request.form['player2'],
        request.form['player3'], request.form['player4']
    ]
    team1_name_from_form = request.form['team1_name']
    team2_name_from_form = request.form['team2_name']

    if any(name == "" for name in players):
        return redirect(url_for('index'))

    session['team1_name'] = team1_name_from_form if team1_name_from_form else "Takım A"
    session['team2_name'] = team2_name_from_form if team2_name_from_form else "Takım B"

    session['players'] = players
    session['teams'] = {
        session['team1_name']: [players[2], players[0]],
        session['team2_name']: [players[3], players[1]]
    }

    session['scores'] = {session['team1_name']: 0, session['team2_name']: 0}
    session['current_hand'] = 1
    session['results'] = []

    return redirect(url_for('index'))


@app.route('/save_hand', methods=['POST'])
def save_hand():
    """Her elin sonucunu kaydeden, özel bitiş durumlarına göre puanları hesaplayan fonksiyon."""
    if 'current_hand' not in session or session['current_hand'] > 11:
        return redirect(url_for('index'))

    okey_color = request.form['okey_color']
    penalty_points = int(request.form['penalty_points'])
    winning_player = request.form['winning_player']
    # YENİ: Checkbox'ların durumunu kontrol et
    is_okey_finish = request.form.get('okey_atildi') is not None
    is_cifte_finish = request.form.get('cifte_bitildi') is not None

    winner_team = None
    for team, players_in_team in session['teams'].items():
        if winning_player in players_in_team:
            winner_team = team
            break

    if not winner_team:
        return "Hata: Oyuncu bir takıma ait değil.", 400

    katsayi = OKEY_KATSAYILARI[okey_color]['katsayi']

    # YENİ: Puanları özel bitiş durumuna göre hesapla
    is_special_finish = is_okey_finish or is_cifte_finish
    if is_special_finish:
        ceza = katsayi * penalty_points * 2
        duser_puani = katsayi * 100
        duser_katsayi_klasik = katsayi * 10
    else:
        ceza = katsayi * penalty_points
        duser_puani = katsayi * 10
        duser_katsayi_klasik = katsayi

    losing_team = session['team2_name'] if winner_team == session['team1_name'] else session['team1_name']
    session['scores'][losing_team] += ceza
    session['scores'][winner_team] -= duser_puani

    # YENİ: Hangi türde bitiş yapıldığını sakla
    finish_type = 'normal'
    if is_okey_finish:
        finish_type = 'okey'
    elif is_cifte_finish:
        finish_type = 'cifte'

    hand_result = {
        "el": session['current_hand'],
        "okey": okey_color,
        "kazanan_takim": winner_team,
        "kazanan_oyuncu": winning_player,
        "duser_katsayi": duser_katsayi_klasik,
        "duser": duser_puani,
        "sayilar": penalty_points,
        "ceza": ceza,
        "finish_type": finish_type  # DEĞİŞTİ: Arayüzde kullanılacak bitiş türü
    }
    session['results'].append(hand_result)

    session['current_hand'] += 1
    session.modified = True

    return redirect(url_for('index'))


@app.route('/reset')
def reset():
    """Oyunu sıfırlar ve başlangıç ekranına döner."""
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
