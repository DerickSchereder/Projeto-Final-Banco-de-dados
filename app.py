import os
from flask import Flask, render_template, request
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Função obter conexão com o banco de dados
def obter_conexao():
    return psycopg2.connect(
        host     =   os.getenv("DB_HOST"),
        database =   os.getenv("DB_NAME"),
        user     =   os.getenv("DB_USER"),
        password =   os.getenv("DB_PASSWORD"),
        port     =   os.getenv("DB_PORT")
    )
# ----------------- ROTA DE PACOTES -----------------
@app.route('/')
@app.route('/pacotes')
def pacotes():
    conn = obter_conexao()
    cursor = conn.cursor()
    
    # Busca os pacotes no banco
    cursor.execute("""
        SELECT id_pacote, nome_cidade, nome_hotel, preco_pacote 
        FROM Pacotes 
        JOIN Cidade USING (id_cidade)
        JOIN Hoteis USING (id_hotel);
    """)
    dados_pacotes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('pacotes.html', lista_pacotes=dados_pacotes)

# ----------------- ROTA DE VOOS -----------------
@app.route('/voos', methods=['GET', 'POST'])
def voos():
    conn = obter_conexao()
    cursor = conn.cursor()
    
    # Busca todos os aeroportos para botar nas opções clicáveis no HTML
    cursor.execute("SELECT iata_aeroporto, nome_aeroporto FROM Aeroporto ORDER BY nome_aeroporto;")
    lista_aeroportos = cursor.fetchall()
    
    resultados_voos = []
    
    # Se o usuário clicou em "Buscar" (POST)
    if request.method == 'POST':
        origem = request.form.get('origem')
        destino = request.form.get('destino')
        
        cursor.execute("""
            SELECT 
                vd.id_rota_viagem,
                vd.origem,
                vd.destino,
                TO_CHAR(v.partida_prevista, 'HH24:MI') AS hora_partida,
                TO_CHAR(v.chegada_prevista, 'HH24:MI') AS hora_chegada,
                vd.duracao_estimada,
                vd.numero_paradas,
                ccv.tarifa,
                comp.nome_companhia
            FROM viagens_disponiveis vd
            JOIN trecho_rota_viagem trv USING (id_rota_viagem)
            JOIN voo v USING (id_rota_voo)
            JOIN rota_voo rv USING (id_rota_voo)
            JOIN companhia_aerea comp USING (iata_companhia)
            JOIN classes_com_vaga ccv USING (id_voo)
            WHERE vd.origem = %s AND vd.destino = %s
            ORDER BY ccv.tarifa ASC;
        """, (origem[:3].upper(), destino[:3].upper())) 
        
        resultados_voos = cursor.fetchall()
        
    cursor.close()
    conn.close()
        
    return render_template('voos.html', voos=resultados_voos, aeroportos=lista_aeroportos)

if __name__ == '__main__':
    modo_debug = os.getenv("FLASK_DEBUG") == "True"
    app.run(debug=modo_debug)