from flask import Flask, render_template, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import openai

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carros.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

openai.api_key = ''

db = SQLAlchemy(app)

# Modelos
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, unique=True)
    senha = db.Column(db.String(150), nullable=False)
    carro = db.relationship('Carro', backref='usuario', uselist=False)

class Carro(db.Model):
    __tablename__ = "carro"
    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer, nullable=False)
    modelo = db.Column(db.String(100), nullable=False)
    motorizacao = db.Column(db.String(100), nullable=False)
    potencia = db.Column(db.String(100), nullable=False)
    cor = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200), nullable=False)
    vendedor = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    contato = db.Column(db.String(100), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

    def __repr__(self):
        return f"<Carro {self.modelo}>"

# Criacional: Factory Method
class CarroFactory:
    @staticmethod
    def criar_carro(ano, modelo, motorizacao, potencia, cor, image, vendedor, preco, contato, usuario_id):
        preco = preco.replace('.', '')
        preco_float = float(preco)
        return Carro(ano=ano, modelo=modelo, motorizacao=motorizacao, potencia=potencia, cor=cor, image=image, vendedor=vendedor, preco=preco_float, contato=contato, usuario_id=usuario_id)


# Estrutural: Fachada
class CarroFacade:
    @staticmethod
    def adicionar_carro(carro):
        db.session.add(carro)
        db.session.commit()

    @staticmethod
    def obter_carros():
        return Carro.query.all()

    @staticmethod
    def obter_carro_por_id(carro_id):
        return Carro.query.get(carro_id)

    @staticmethod
    def excluir_carro(carro):
        db.session.delete(carro)
        db.session.commit()

    @staticmethod
    def atualizar_carro(carro):
        db.session.commit()

# Comportamental: Command
class Command:
    def execute(self):
        pass

class CadastrarCarroCommand(Command):
    def __init__(self, form_data, usuario_id):
        self.form_data = form_data
        self.usuario_id = usuario_id

    def execute(self):
        carro = CarroFactory.criar_carro(
            ano=self.form_data['ano'],
            modelo=self.form_data['modelo'],
            motorizacao=self.form_data['motorizacao'],
            potencia=self.form_data['potencia'],
            cor=self.form_data['cor'],
            image=self.form_data['image'],
            vendedor=self.form_data['vendedor'],
            preco=self.form_data['preco'],
            contato=self.form_data['contato'],
            usuario_id=self.usuario_id
        )
        CarroFacade.adicionar_carro(carro)

class EditarCarroCommand(Command):
    def __init__(self, carro, form_data):
        self.carro = carro
        self.form_data = form_data

    def execute(self):
        self.carro.ano = self.form_data['ano']
        self.carro.modelo = self.form_data['modelo']
        self.carro.motorizacao = self.form_data['motorizacao']
        self.carro.potencia = self.form_data['potencia']
        self.carro.cor = self.form_data['cor']
        self.carro.image = self.form_data['image']
        self.carro.vendedor = self.form_data['vendedor']
        self.carro.preco = self.form_data['preco']
        self.carro.contato = self.form_data['contato']
        CarroFacade.atualizar_carro(self.carro)

class ExcluirCarroCommand(Command):
    def __init__(self, carro):
        self.carro = carro

    def execute(self):
        CarroFacade.excluir_carro(self.carro)

# Funções auxiliares
def perguntar(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"Error: {e}"

# Rotas
@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def home():
    try:
        carros = CarroFacade.obter_carros()
        resposta = session.pop('resposta', '')
        return render_template('index.html', carros=carros, resposta=resposta)
    except Exception as e:
        return f"An error occurred: {e}"


@app.route('/sobre')
def sobre():
    texto = """
    <title>Sobre</title>
    BimmerMotors é uma renomada concessionária de automóveis, especializada na venda de carros de alta qualidade e desempenho excepcional. Fundada em 2024, nossa missão é proporcionar uma experiência de compra única e personalizada para cada cliente.
<p>
    Localizada no coração da cidade, a BimmerMotors oferece uma ampla variedade de veículos, desde elegantes sedans até potentes SUVs e carros esportivos de luxo. Nossa equipe de especialistas em automóveis está comprometida em ajudar os clientes a encontrar o carro dos seus sonhos, oferecendo orientação profissional e conhecimento especializado em cada etapa do processo de compra.
<p>
    Na BimmerMotors, valorizamos a transparência, integridade e excelência no atendimento ao cliente. Nossos carros são cuidadosamente selecionados e inspecionados para garantir a mais alta qualidade e confiabilidade. Além disso, oferecemos serviços de financiamento flexíveis e opções de garantia para atender às necessidades individuais de cada cliente.
<p>
    Se você está procurando um carro premium com desempenho excepcional e estilo incomparável, visite a BimmerMotors hoje mesmo e descubra a emoção de dirigir o carro dos seus sonhos. Sua jornada para o luxo automotivo começa aqui na BimmerMotors - onde a paixão pelos carros encontra a excelência no atendimento ao cliente.
    """
    return texto


@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if 'username' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.filter_by(nome=session['username']).first()
    if usuario.carro:
        return 'Você já possui um anúncio ativo.'

    if request.method == 'POST':
        command = CadastrarCarroCommand(request.form, usuario.id)
        command.execute()
        return redirect(url_for('home'))

    return render_template('cadastrar.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if 'username' not in session:
        return redirect(url_for('login'))

    carro = CarroFacade.obter_carro_por_id(id)
    if carro.usuario.nome != session['username']:
        return 'Você não tem permissão para editar este anúncio.'

    if request.method == 'POST':
        command = EditarCarroCommand(carro, request.form)
        command.execute()
        return redirect(url_for('home'))

    editar_html = """
    <title>Editar Carro</title>
    <form action="{{ url_for('editar', id=carro.id) }}" method="post">
        <label for="vendedor">Nome do Vendedor:</label>
        <input type="text" id="vendedor" name="vendedor" value="{{ carro.vendedor }}" required>

        <label for="preco">Preço:</label>
        <input type="text" id="preco" name="preco" value="{{ carro.preco }}" required>

        <label for="ano">Ano:</label>
        <input type="number" id="ano" name="ano" value="{{ carro.ano }}" required>

        <label for="modelo">Modelo:</label>
        <input type="text" id="modelo" name="modelo" value="{{ carro.modelo }}" required>

        <label for="motorizacao">Motorização:</label>
        <input type="text" id="motorizacao" name="motorizacao" value="{{ carro.motorizacao }}" required>

        <label for="potencia">Potência:</label>
        <input type="text" id="potencia" name="potencia" value="{{ carro.potencia }}" required>

        <label for="cor">Cor:</label>
        <input type="text" id="cor" name="cor" value="{{ carro.cor }}" required>

        <label for="image">URL da Imagem:</label>
        <input type="url" id="image" name="image" value="{{ carro.image }}" required>

        <label for="contato">Contato:</label>
        <input type="text" id="contato" name="contato" value="{{ carro.contato }}" required>

        <input type="submit" value="Salvar Alterações">
    </form>
    """
    return render_template_string(editar_html, carro=carro)

@app.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    if 'username' not in session:
        return redirect(url_for('login'))

    carro = CarroFacade.obter_carro_por_id(id)
    if carro.usuario.nome != session['username']:
        return 'Você não tem permissão para excluir este anúncio.'

    command = ExcluirCarroCommand(carro)
    command.execute()
    return redirect(url_for('home'))

@app.route('/usuario', methods=['POST', 'GET'])
def addUsuario():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']

        if Usuario.query.filter_by(nome=nome).first():
            return 'Já existe um usuário com esse nome.'

        usuario = Usuario(nome=nome, senha=senha)
        db.session.add(usuario)
        db.session.commit()
        return redirect(url_for('login'))

    add_usuario_html = """
    <title>Adicionar Usuário</title>
    <p>Faça seu cadastro:</p>
    <form action="{{ url_for('addUsuario') }}" method="post">
        <label for="nome">Nome:</label>
        <input type="text" id="nome" name="nome" required>

        <label for="senha">Senha:</label>
        <input type="password" id="senha" name="senha" required>

        <input type="submit" value="Adicionar Usuário">
    </form>
    """
    return render_template_string(add_usuario_html)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']

        usuario = Usuario.query.filter_by(nome=nome, senha=senha).first()
        if usuario:
            session['username'] = usuario.nome
            return redirect(url_for('home'))
        else:
            return 'Nome ou senha incorretos.'

    login_html = """
    <title>Login</title>
    <p>Login
    <form action="{{ url_for('login') }}" method="post">
        <label for="nome">Nome:</label>
        <input type="text" id="nome" name="nome" required>

        <label for="senha">Senha:</label>
        <input type="password" id="senha" name="senha" required>

        <input type="submit" value="Login">
    </form>
    """
    return render_template_string(login_html)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/recomendar', methods=['GET', 'POST'])
def recomendar():
    if request.method == 'POST':
        resposta = None
        try:
            preferencia = request.form['preferencia']
            orcamento = request.form['orcamento']
            uso = request.form['uso']

            print(f"Preferencia: {preferencia}, Orcamento: {orcamento}, Uso: {uso}")

            prompt = f"Baseado nas seguintes preferências, orçamentos e usos, recomende um estilo de carro: Preferência: {preferencia}, Orçamento: {orcamento}, Uso: {uso}."
            resposta = perguntar(prompt)

            print(f"Resposta do GPT-3: {resposta}")
        except Exception as e:
            print(f"An error occurred: {e}")
            return f"An error occurred: {e}", 500

        return render_template('recomendar.html', resposta=resposta)


    return render_template('recomendar.html')


if __name__ == '__main__':
    app.run(debug=True)
