from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, datetime
import csv




#helpers
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

#helpers






# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'



# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///database.db")


@app.route("/")
#@login_required
def index():
    vendas = db.execute("SELECT data_venda, id_venda, cliente, senha FROM vendas  WHERE entregue=0 ORDER BY data_venda")
    for venda in vendas:
        venda['produtos'] = db.execute("SELECT produtos.nome_produto,vendas_detalhadas.qtd FROM vendas_detalhadas INNER JOIN produtos ON vendas_detalhadas.id_produto = produtos.id_produto WHERE vendas_detalhadas.id_venda = :id_venda",id_venda=venda['id_venda'])
    return render_template('index.html',vendas=vendas)


@app.route("/entrega", methods=["GET", "POST"])
#@login_required
def entrega():
    if request.method == 'POST':
        id_venda = request.form['id']
        db.execute("UPDATE vendas SET entregue = 1 WHERE id_venda=:id_venda",id_venda=id_venda)
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("usuário em branco", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("senha em branco", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("usuário ou senha inválido", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        confpassword = request.form['confirmation']
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))


        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("usuário em branco", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("senha em branco", 403)
        # Ensure password was submitted
        elif password != confpassword:
            return apology("senhas não combinam", 403)
        elif len(rows) != 0:
            return apology("usuário já cadastrado", 403)
        else:
            password = generate_password_hash(password)
            db.execute("INSERT INTO users(username, hash) VALUES (:username, :hash);", username=username, hash=password)
            # Redirect user to home page
            return redirect("/")


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



@app.route("/produtos")
#@login_required
def produtos():
    lista_produtos = db.execute("SELECT id_produto, nome_produto, preco, nome_categoria FROM produtos INNER JOIN categorias ON produtos.id_categoria = categorias.id_categoria WHERE produtos.ativo = 1 ORDER BY produtos.nome_produto ASC")
    admin = False
    return render_template('produtos.html', lista_produtos=lista_produtos,admin=admin)

@app.route("/produtosadmin", methods=["GET", "POST"])
@login_required
def produtosadmin():
    if request.method == 'POST':
        id_produto = request.form['id_produto']
        db.execute("UPDATE produtos SET ativo=0 WHERE id_produto=:id_produto",id_produto=id_produto)
        return redirect('/produtosadmin')
    else:
        lista_produtos = db.execute("SELECT id_produto, nome_produto, preco, nome_categoria FROM produtos INNER JOIN categorias ON produtos.id_categoria = categorias.id_categoria WHERE produtos.ativo = 1 ORDER BY produtos.nome_produto ASC")
        admin = True
        return render_template('produtos.html', lista_produtos=lista_produtos,admin=admin)

@app.route("/novoproduto", methods=["GET", "POST"])
@login_required
def novo_produto():
    if request.method == "POST":
        nome = request.form['nome']
        preco = request.form['preco']
        categoria = request.form['categoria']

        rows = db.execute("SELECT * FROM produtos WHERE nome_produto = :nome", nome=request.form.get("nome"))



        if not request.form.get("nome"):
            return apology("nome do produto obrigatório", 403)


        elif not request.form.get("preco"):
            return apology("preco obrigatório", 403)

        elif len(rows) != 0:
            return apology("produto já cadastrado", 403)
        else:
            id_categoria = db.execute("SELECT id_categoria FROM categorias WHERE nome_categoria=:categoria",categoria=categoria)
            id_categoria = id_categoria[0]['id_categoria']
            db.execute("INSERT INTO produtos (nome_produto,preco,id_categoria, ativo) VALUES (:nome, :preco, :id_categoria, 1);", nome=nome, preco=preco, id_categoria=id_categoria)

            # Redirect user to home page
            return redirect("/")


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        lista_categorias = db.execute("SELECT nome_categoria FROM categorias")
        return render_template("novoproduto.html",lista_categorias=lista_categorias)




@app.route("/venda", methods=["GET", "POST"])
#@login_required
def venda():
    from datetime import date, datetime
    if request.method == "POST":
        db.execute("DELETE FROM venda_temporaria")
        lista_produtos = db.execute("SELECT nome_produto FROM produtos")
        senha = db.execute("SELECT senha FROM senhas")[0]['senha']
        now = datetime.now()
        data_venda = now.strftime("%Y-%m-%d %H:%M:%S")
        cliente = request.form['cliente']
        for produto in lista_produtos:
            produto = produto['nome_produto']
            qtd = request.form[produto]
            if not qtd == "":
                if int(qtd) > 0:
                    qtd = int(qtd)
                    id_produto = db.execute("SELECT id_produto FROM produtos WHERE nome_produto=:produto", produto=produto)
                    id_produto = id_produto[0]['id_produto']
                    total_produto = db.execute("SELECT preco FROM produtos WHERE nome_produto=:produto", produto=produto)
                    total_produto = total_produto[0]['preco'] * qtd
                    db.execute(
                        "INSERT INTO venda_temporaria (nome_produto,id_produto,qtd, total_produtos,data_venda,cliente,senha) VALUES (:nome_produto,:id_produto, :qtd, :valor,:data_venda,:cliente,:senha)",
                         nome_produto=produto,id_produto=id_produto, qtd=qtd, valor=total_produto,data_venda=data_venda,cliente=cliente,senha=senha)

        cf_venda = db.execute("SELECT * FROM venda_temporaria")
        total_compra = db.execute("SELECT SUM(total_produtos) FROM venda_temporaria")[0]['SUM(total_produtos)']

        return render_template("confirmarvenda.html",cf_venda=cf_venda,total_compra=total_compra,cliente=cliente)


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        lista_categorias = db.execute("SELECT nome_categoria FROM categorias")
        prod_categorias = []
        for categoria in lista_categorias:
            categoria = categoria['nome_categoria']
            id_categoria = \
            db.execute("SELECT id_categoria FROM categorias WHERE nome_categoria=:categoria", categoria=categoria)[0][
                'id_categoria']
            lista_produtos = db.execute("SELECT nome_produto, preco FROM produtos WHERE id_categoria=:id_categoria",
                                        id_categoria=id_categoria)
            prod_categorias.append(
                {"categoria": categoria, "lista_produtos": lista_produtos, 'id_categoria': id_categoria})

        return render_template("venda.html", prod_categorias=prod_categorias)


@app.route("/confirmarvenda", methods=["GET", "POST"])
#@login_required
def confirmarvenda():
    from datetime import datetime
    venda = db.execute("SELECT * FROM venda_temporaria")
    senha = db.execute("SELECT DISTINCT senha FROM venda_temporaria")[0]['senha']
    now = datetime.now()
    data_venda = now.strftime("%Y-%m-%d %H:%M:%S")
    cliente = db.execute("SELECT DISTINCT cliente FROM venda_temporaria")[0]['cliente']
    total_venda = db.execute("SELECT SUM(total_produtos) FROM venda_temporaria")[0]["SUM(total_produtos)"]
    db.execute("INSERT INTO vendas (data_venda, entregue,total, cliente,senha) VALUES (:data_venda, 0,:total,:cliente,:senha)",
               data_venda=data_venda, total=total_venda,cliente=cliente,senha=senha)

    key = db.execute("SELECT MAX(id_venda) FROM vendas")[0]['MAX(id_venda)']
    for produtos in venda:
        id_produto =produtos['id_produto']
        qtd = produtos['qtd']
        total_produtos = produtos['total_produtos']
        db.execute("INSERT INTO vendas_detalhadas (id_venda, id_produto, qtd, total_produtos) VALUES (:id_venda, :id_produto, :qtd, :total_produtos)",
                   id_venda=key, id_produto=id_produto, qtd=qtd, total_produtos=total_produtos)
        db.execute("UPDATE senhas SET senha=:nova_senha",nova_senha = senha+1)
    return redirect("/")


@app.route("/gerenciarcategoria", methods=["GET", "POST"])
@login_required
def gerenciarcategoria():
    if request.method == "POST":
        nome_categoria = request.form['nome_categoria']
        ordem = db.execute("SELECT ordem FROM categorias WHERE nome_categoria = :nome_categoria",nome_categoria=nome_categoria)[0]['ordem']

        return render_template("editarcategoria.html", nome_categoria=nome_categoria,ordem=ordem)
    else:
        lista_categorias = db.execute("SELECT nome_categoria FROM categorias ORDER BY ordem")
        prod_categorias = []
        for categoria in lista_categorias:
            categoria = categoria['nome_categoria']
            id_categoria = db.execute("SELECT id_categoria FROM categorias WHERE nome_categoria=:categoria",categoria=categoria)[0]['id_categoria']
            lista_produtos = db.execute("SELECT nome_produto, preco FROM produtos WHERE id_categoria=:id_categoria",id_categoria=id_categoria)
            ordem = db.execute("SELECT ordem FROM categorias WHERE nome_categoria=:categoria",categoria=categoria)[0]['ordem']
            prod_categorias.append({"categoria": categoria, "lista_produtos":lista_produtos, 'ordem':ordem})

        return render_template("gerenciarcategorias.html", prod_categorias=prod_categorias)

@app.route("/criarcategoria", methods=["GET", "POST"])
@login_required
def criar_categoria():
    if request.method == "POST":
        nome = request.form['nome']

        rows = db.execute("SELECT * FROM categorias WHERE nome_categoria = :nome", nome=nome)
        if not request.form.get("nome"):
            return apology("nome do produto obrigatório", 403)

        elif len(rows) != 0:
            return apology("categoria já cadastrado", 403)
        else:
            db.execute("INSERT INTO categorias (nome_categoria) VALUES (:nome);", nome=nome)
            ordem = db.execute("SELECT MAX(ordem) FROM categorias")[0]['MAX(ordem)']
            ordem += 1
            db.execute("UPDATE categorias SET ordem=:ordem WHERE nome_categoria = :nome_categoria",ordem=ordem, nome_categoria=nome)
            # Redirect user to home page
            return redirect("/")


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("criarcategoria.html")

@app.route("/todasvendas", methods=["GET", "POST"])
#@login_required
def todasvendas():
    if request.method == 'POST':
        id = request.form['id']
        data_venda = db.execute("SELECT data_venda FROM vendas WHERE id_venda=:id",id=id)[0]['data_venda']
        entregue = db.execute("SELECT entregue FROM vendas WHERE id_venda=:id",id=id)[0]['entregue']
        if entregue == 0:
            entregue = 'Não'
        else:
            entregue = 'Sim'
        dados = db.execute("SELECT produtos.nome_produto, vendas_detalhadas.qtd, vendas_detalhadas.total_produtos FROM vendas_detalhadas INNER JOIN produtos ON vendas_detalhadas.id_produto = produtos.id_produto WHERE vendas_detalhadas.id_venda=:id",id=id)
        total = 0
        for item in dados:
            total += float(item['total_produtos'])
        return render_template('vendadetalhada.html', id=id, data_entrega=data_venda, entregue=entregue,dados=dados, total=total)
    else:
        lista_vendas = db.execute("SELECT * FROM vendas ORDER BY data_venda DESC")
        return render_template('todasvendas.html', lista_vendas=lista_vendas)





@app.route("/graficos", methods=["GET", "POST"])
@login_required
def graficos():
    if request.method == 'POST':
        from random import randint
        nome_categoria = request.form['categoria']
        if nome_categoria != "Todos":
            id_categoria = db.execute("SELECT id_categoria FROM categorias WHERE nome_categoria = :categoria",categoria=nome_categoria)[0]['id_categoria']
            produtos_por_categoria = []
            lista_categoria = {}
            values = []
            labels = []
            colors = []
            vazia = False
            lista_categoria['id_categoria'] = id_categoria
            lista_categoria['produtos'] = \
                db.execute("SELECT id_produto,nome_produto FROM produtos WHERE id_categoria=:id_categoria", id_categoria=id_categoria)
            for produto in lista_categoria['produtos']:
                id_produto = produto['id_produto']
                produto['qtd_vendas'] = \
                db.execute("SELECT SUM(qtd) FROM vendas_detalhadas WHERE id_produto=:id_produto", id_produto=id_produto)[0]['SUM(qtd)']
                if produto['qtd_vendas'] is None:
                    produto['qtd_vendas'] = 0
                labels.append(produto['nome_produto'])
                values.append(produto['qtd_vendas'])
                colors.append("#" + (hex(randint(0, 16777215))[2:]).upper())
                set =zip(values, labels, colors)
                if values == [0]:
                    vazia = True
                produtos_por_categoria.append(lista_categoria)
            return render_template('graficos.html', set=set, nome_categoria=nome_categoria, vazia=vazia)
        else:
            todos_produtos = []
            values = []
            labels = []
            colors = []
            id_produtos = db.execute("SELECT id_produto FROM produtos")
            for id in id_produtos:
                produto = {}
                produto['id'] = id['id_produto']
                produto['nome'] = db.execute("SELECT nome_produto FROM produtos WHERE id_produto = :id_produto",id_produto=produto['id'])[0]['nome_produto']
                produto['qtd'] = db.execute("SELECT SUM(qtd) FROM vendas_detalhadas WHERE id_produto = :id_produto",id_produto=produto['id'])[0]['SUM(qtd)']
                if produto['qtd'] is None:
                    produto['qtd'] = 0

                todos_produtos.append(produto)
                values.append(produto['qtd'])
                labels.append(produto['nome'])
                colors.append("#" + (hex(randint(0, 16777215))[2:]).upper())

            set = zip(values, labels, colors)

            return render_template('graficos.html', set=set, nome_categoria=nome_categoria,vazia=False)
    else:
        categorias = db.execute("SELECT nome_categoria FROM categorias")
        categorias.append({'nome_categoria':'Todos'})
        return render_template('escolhergraficos.html',lista_categorias=categorias)

@app.route("/gerarcsv")
@login_required
def gerarcsv():
    #categorias
    with open('categorias.csv','w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id_categoria','nome_categoria'])
        linhas = db.execute("SELECT * from categorias")
        for item in linhas:
            writer.writerow([item['id_categoria'],item['nome_categoria']])

    #produtos
    with open('produtos.csv','w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id_produto', 'nome_produto', 'preco', 'id_categoria'])
        linhas = db.execute("SELECT * from produtos")
        for item in linhas:
            writer.writerow([item['id_produto'], item['nome_produto'], item['preco'], item['id_categoria']])

    # vendas
    with open('vendas.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id_venda', 'data_venda', 'entregue', 'total'])
        linhas = db.execute("SELECT * from vendas")
        for item in linhas:
            writer.writerow([item['id_venda'], item['data_venda'], item['entregue'], item['total']])

    # vendas detalhadas
    with open('vendas_detalhadas.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id_venda', 'id_produto', 'qtd', 'total_produtos'])
        linhas = db.execute("SELECT * from vendas_detalhadas")
        for item in linhas:
            writer.writerow([item['id_venda'], item['id_produto'], item['qtd'], item['total_produtos']])

   

    return redirect("/")


@app.route("/editarcategoria", methods=["GET", "POST"])
@login_required
def editarcategoria():
    novo_nome = request.form['novo_nome']
    nova_ordem = request.form['ordem']
    velho_nome = request.form['velho_nome']
    db.execute("UPDATE categorias SET nome_categoria = :novo_nome, ordem = :nova_ordem WHERE nome_categoria = :velho_nome ",
               novo_nome=novo_nome, nova_ordem=nova_ordem, velho_nome=velho_nome)
    return redirect('/gerenciarcategoria')


@app.route("/senha", methods=["GET", "POST"])
@login_required
def senha():
    if request.method == "POST":
        db.execute("UPDATE senhas SET senha=1")
        return redirect('/senha')
    else:
        senha = db.execute("SELECT senha FROM senhas")[0]['senha']
        return render_template("senha.html",senha=senha)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


if __name__ == '__main__':
    app.run()





