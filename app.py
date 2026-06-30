import os
from flask import Flask, render_template, request, session, redirect, url_for
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Chave para permitir o uso de sessões (carrinho)
app.secret_key = os.getenv("SECRET_KEY", "chave")

# Função obter conexão com o banco de dados
def obter_conexao():
    return psycopg2.connect(
        host     =   os.getenv("DB_HOST"),
        database =   os.getenv("DB_NAME"),
        user     =   os.getenv("DB_USER"),
        password =   os.getenv("DB_PASSWORD"),
        port     =   os.getenv("DB_PORT")
    )

# ----------------- ROTAS DO CARRINHO -----------------

@app.route('/carrinho')
def ver_carrinho():
    # Pega o carrinho da sessão. Se não existir, inicia uma lista vazia.
    itens_carrinho = session.get('carrinho', [])
    
    # Calcula o valor total somando o preço de cada item
    valor_total = sum(float(item['preco']) for item in itens_carrinho)
    
    return render_template('carrinho.html', itens_carrinho=itens_carrinho, valor_total=valor_total)


@app.route('/carrinho/adicionar', methods=['POST'])
def adicionar_carrinho():
    # Inicializa o carrinho na sessão caso ele não exista
    if 'carrinho' not in session:
        session['carrinho'] = []
    
    # Captura os dados enviados pelo botão do formulário
    tipo = request.form.get('tipo')
    nome = request.form.get('nome')
    detalhes = request.form.get('detalhes')
    preco = request.form.get('preco')
    
    # Cria o dicionário do produto
    novo_item = {
        'tipo': tipo,
        'nome': nome,
        'detalhes': detalhes,
        'preco': float(preco)
    }
    
    # Adiciona no carrinho e avisa a sessão que houve modificação
    carrinho_atual = session['carrinho']
    carrinho_atual.append(novo_item)
    session['carrinho'] = carrinho_atual
    
    return redirect(url_for('ver_carrinho'))


@app.route('/carrinho/remover/<int:indice>', methods=['POST'])
def remover_carrinho(indice):
    if 'carrinho' in session:
        carrinho_atual = session['carrinho']
        if 0 <= indice < len(carrinho_atual):
            carrinho_atual.pop(indice) # Remove o item pelo índice da lista
            session['carrinho'] = carrinho_atual
            
    return redirect(url_for('ver_carrinho'))


@app.route('/carrinho/finalizar', methods=['POST'])
def finalizar_carrinho():
    # Limpa o carrinho após finalizar a compra
    session.pop('carrinho', None)
    return "<h1>Compra finalizada com sucesso! Obrigado por viajar conosco.</h1>"

# ----------------- ROTA DE PACOTES -----------------
@app.route('/')
@app.route('/pacotes')
def pacotes():
    conn = obter_conexao()
    cursor = conn.cursor()
    
    # Busca todos pacotes e checa a disponibilidade cruzando com as views de voos
    cursor.execute("""
        SELECT 
            p.id_pacote, 
            cid.nome_cidade, 
            h.nome_hotel, 
            p.categoria_pacote, 
            p.duracao_pacote, 
            p.preco_pacote,
            CASE 
                WHEN vd_ida.id_rota_viagem IS NOT NULL AND vd_volta.id_rota_viagem IS NOT NULL 
                THEN 1 ELSE 0 
            END as disponivel
        FROM Pacotes p
        JOIN Cidade cid ON p.id_cidade = cid.id_cidade
        JOIN Hoteis h ON p.id_hotel = h.id_hotel
        LEFT JOIN viagens_disponiveis vd_ida ON p.id_rota_ida = vd_ida.id_rota_viagem
        LEFT JOIN viagens_disponiveis vd_volta ON p.id_rota_volta = vd_volta.id_rota_viagem
        ORDER BY disponivel DESC, p.preco_pacote ASC;
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

# ----------------- ROTA: CARRINHOS COM MAIS DE 1 PACOTE -----------------
@app.route('/carrinhos-acumulados')
def carrinhos_acumulados():
    conn = obter_conexao()
    cursor = conn.cursor()
    
    # Executa a sua consulta exatamente como você definiu
    cursor.execute("""
        SELECT id_carrinho, nome_cliente, SUM(quantidade) AS total_pacotes
        FROM Cliente 
        NATURAL JOIN Carrinho 
        NATURAL JOIN Item_Pacote
        GROUP BY id_carrinho, nome_cliente
        HAVING SUM(quantidade) > 1;
    """)
    resultados = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Envia os dados para a nova página HTML
    return render_template('carrinho_com_pacote.html', dados_relatorio=resultados)

if __name__ == '__main__':
    modo_debug = os.getenv("FLASK_DEBUG") == "True"
    app.run(debug=modo_debug)