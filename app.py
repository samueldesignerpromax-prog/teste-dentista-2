import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

app = Flask(__name__)

# Conectar ao MongoDB (usando variável de ambiente)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URI)
db = client.dentista_db

# Coleções
dentistas_col = db.dentistas
servicos_col = db.servicos
agendamentos_col = db.agendamentos

# Inicializar dados de exemplo se estiver vazio (apenas para demo)
def init_db():
    if dentistas_col.count_documents({}) == 0:
        dentistas_col.insert_many([
            {"nome": "Dra. Ana", "especialidade": "Ortodontia"},
            {"nome": "Dr. Carlos", "especialidade": "Implantodontia"},
            {"nome": "Dra. Beatriz", "especialidade": "Endodontia"}
        ])
    if servicos_col.count_documents({}) == 0:
        servicos_col.insert_many([
            {"nome": "Limpeza", "duracao": 30},
            {"nome": "Obturação", "duracao": 45},
            {"nome": "Clareamento", "duracao": 60},
            {"nome": "Canal", "duracao": 90}
        ])

# Chamar no início (se não existir, cria)
init_db()

# ================== ROTAS ==================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dentistas')
def listar_dentistas():
    dentistas = list(dentistas_col.find())
    return render_template('lista.html', titulo="Dentistas", itens=dentistas, tipo="dentista")

@app.route('/servicos')
def listar_servicos():
    servicos = list(servicos_col.find())
    return render_template('lista.html', titulo="Serviços", itens=servicos, tipo="servico")

@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if request.method == 'POST':
        # Pegar dados do formulário
        nome = request.form['nome']
        telefone = request.form['telefone']
        email = request.form.get('email', '')
        dentista_id = request.form['dentista_id']
        servico_id = request.form['servico_id']
        data_hora_str = request.form['data_hora']  # formato "YYYY-MM-DDTHH:MM"
        data_hora = datetime.fromisoformat(data_hora_str)

        # Inserir agendamento
        agendamento = {
            "cliente_nome": nome,
            "cliente_telefone": telefone,
            "cliente_email": email,
            "dentista_id": ObjectId(dentista_id),
            "servico_id": ObjectId(servico_id),
            "data_hora": data_hora,
            "status": "agendado",
            "criado_em": datetime.utcnow()
        }
        result = agendamentos_col.insert_one(agendamento)
        return redirect(url_for('agendamentos'))

    # GET: mostrar formulário
    dentistas = list(dentistas_col.find())
    servicos = list(servicos_col.find())
    return render_template('agendar.html', dentistas=dentistas, servicos=servicos)

@app.route('/agendamentos')
def agendamentos():
    # Buscar agendamentos com os dados dos dentistas e serviços (populate)
    ags = list(agendamentos_col.aggregate([
        {
            "$lookup": {
                "from": "dentistas",
                "localField": "dentista_id",
                "foreignField": "_id",
                "as": "dentista"
            }
        },
        {
            "$lookup": {
                "from": "servicos",
                "localField": "servico_id",
                "foreignField": "_id",
                "as": "servico"
            }
        },
        {"$unwind": "$dentista"},
        {"$unwind": "$servico"},
        {"$sort": {"data_hora": 1}}
    ]))
    return render_template('agendamentos.html', agendamentos=ags)

# Rota para cancelar (opcional)
@app.route('/cancelar/<id>')
def cancelar(id):
    agendamentos_col.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"status": "cancelado"}}
    )
    return redirect(url_for('agendamentos'))

# ================== EXECUÇÃO (para desenvolvimento) ==================
if __name__ == '__main__':
    app.run(debug=True)
