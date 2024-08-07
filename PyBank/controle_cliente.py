import textwrap
from abc import ABC, abstractclassmethod, abstractproperty
from datetime import datetime
import re
from pathlib import Path

ROOT_PATH = Path(__file__).parent


class ContasIterador:
    def __init__(self, contas):
        self.contas = contas
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        try:
            conta = self.contas[self._index]
            return f"""\
            Agência:\t{conta.agencia}
            Número:\t\t{conta.numero}
            Titular:\t{conta.cliente.nome}
            Saldo:\t\tR$ {conta.saldo:.2f}
        """
        except IndexError:
            raise StopIteration
        finally:
            self._index += 1


class Cliente:
    def __init__(self, logradouro):
        self.logradouro = logradouro
        self.contas = []
        self.indice_conta = 0

    def realizar_transacao(self, conta, transacao):
        if len(conta.historico.transacoes_do_dia()) >= 5:
            print("\nVocê excedeu o limite de transações permitidas para hoje.")
            return

        transacao.registrar(conta)

    def adicionar_conta(self, conta):
        self.contas.append(conta)


class PessoaFisica(Cliente):
    def __init__(self, nome, data_nascimento, cpf, cep, logradouro, telefone,
                 complemento, bairro, cidade, estado):
        super().__init__(logradouro)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf
        self.cep = cep
        self.logradouro = logradouro
        self.telefone = telefone
        self.cmplemento = complemento
        self.bairro = bairro
        self.cidade = cidade
        self.estado = estado

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: ('{self.nome}', '{self.cpf}')>"


class Conta:
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()

    @classmethod
    def nova_conta(cls, cliente, numero):
        return cls(numero, cliente)

    @property
    def saldo(self):
        return self._saldo

    @property
    def numero(self):
        return self._numero

    @property
    def agencia(self):
        return self._agencia

    @property
    def cliente(self):
        return self._cliente

    @property
    def historico(self):
        return self._historico

    def sacar(self, valor):
        saldo = self.saldo
        excedeu_saldo = valor > saldo

        if excedeu_saldo:
            print("\nVocê não possui saldo suficientepara realizar esta transação.\n")

        elif valor > 0:
            self._saldo -= valor
            print(f"\nVocê sacou R$ {valor}, retire o dinheiro.")
            return True

        else:
            print("\nInforme um valor correto.")

        return False

    def depositar(self, valor):
        if valor > 0:
            self._saldo += valor
            print("\nDepósito realizado com sucesso.")
        else:
            print("\nPor favor, informe um valor válido.")
            return False

        return True


class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite=500, limite_saques=3):
        super().__init__(numero, cliente)
        self._limite = limite
        self._limite_saques = limite_saques

    @classmethod
    def nova_cona(cls, cliente, numero, limite, limite_saques):
        return cls(numero, cliente, limite, limite_saques)

    def sacar(self, valor):
        numero_saques = len(
            [transacao for transacao in self.historico.transacoes
             if transacao["tipo"] == Saque.__name__]
        )

        excedeu_limite = valor > self._limite
        excedeu_saques = numero_saques >= self._limite_saques

        if excedeu_limite:
            print("\nValor superior ao limite permitido para esta conta.")

        elif excedeu_saques:
            print("\nQuantidade de saques diários excedido.")

        else:
            return super().sacar(valor)

        return False

    def __repr__(self):
        return f"<{self.__class__.__name__}: ('{self.agencia}', '{self.numero}', '{self.cliente.nome}')>"

    def __str__(self):
        return f"""\
            Agência:\t{self.agencia}
            C/C:\t\t{self.numero}
            Titular:\t{self.cliente.nome}
            Saldo:\t\tR$ {self.saldo}
        """


class Historico:
    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes

    def adicionar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )

    def gerar_relatorio(self, tipo_transacao=None):
        for transacao in self._transacoes:
            if tipo_transacao is None or transacao["tipo"].lower() == tipo_transacao.lower():
                yield transacao

    def transacoes_do_dia(self):
        data_atual = datetime.now().date()
        transacoes = []
        for transacao in self._transacoes:
            data_transacao = datetime.strptime(transacao["data"], "%d-%m-%Y %H:%M:%S").date()
            if data_atual == data_transacao:
                transacoes.append(transacao)
        return transacoes


class Transacao(ABC):
    @property
    @abstractproperty
    def valor(self):
        pass

    @abstractclassmethod
    def registrar(self, conta):
        pass


class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso_transacao = conta.sacar(self.valor)

        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)


class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso_transacao = conta.depositar(self.valor)

        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)


def log_transacao(func):
    def envelope(*args, **kwargs):
        resultado = func(*args, **kwargs)
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ROOT_PATH / "log.txt", "a") as arquivo:
            arquivo.write(
                f"[{data_hora}] Função '{func.__name__}' executada com argumentos {args} e {kwargs}. "
                f"Retornou {resultado}\n"
            )
        return resultado

    return envelope


def menu():
    menu = """\n
    ======= Bem Vindo(a) ao PyBank ========
    Por favor, digite a opção que deseja:\n
    [1]\tDepositar
    [2]\tSacar
    [3]\tExtrato
    [4]\tCadastrar nova conta
    [5]\tCadastrar novo cliente
    [6]\tLista de contas cadastradas
    [0]\tSair
    \n
    """
    return input(textwrap.dedent(menu))


def filtrar_cliente(cpf, clientes):
    clientes_filtrados = [cliente for cliente in clientes
                          if cliente.cpf == cpf]
    return clientes_filtrados[0] if clientes_filtrados else None


@log_transacao
def depositar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\nNão há cadastro para este CPF, por favor, realize um cadastro.")
        return

    valor = float(input("\nInforme o valor do depósito: "))
    transacao = Deposito(valor)

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, transacao)


def recuperar_conta_cliente(cliente):
    if not cliente.contas:
        print("\nAinda não há uma conta cadastrada para este cliente.")
        return

    # FIXME: não permite cliente escolher a conta
    return cliente.contas[0]


@log_transacao
def sacar(clientes):
    cpf = input("\nInforme o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\nNão há uma conta cadastrada neste CPF.")
        return

    valor = float(input("\nInforme o valor do saque: "))
    transacao = Saque(valor)

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, transacao)


@log_transacao
def exibir_extrato(clientes):
    cpf = input("\nInforme o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\nNão há uma conta cadastrada para este CPF.")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    print("\n=================== EXTRATO ===================")
    extrato = ""
    tem_transacao = False
    for transacao in conta.historico.gerar_relatorio():
        tem_transacao = True
        extrato += f"\n{transacao['data']}\n{transacao['tipo']}:\tR$ {transacao['valor']:.2f}"

    if not tem_transacao:
        extrato = "Sem movimentações."

    print(extrato)
    print(f"\nSaldo:\nR$ {conta.saldo:.2f}")
    print("====================================")


def validate(numero, pattern):

    while not re.match(pattern, numero):
        numero = input("\nInforme seu número de telefone, com o seguinte formato: (XX) XXXXX-XXXX\n")
        if re.match(pattern, numero):
            return numero
        else:
            print("\nPor favor, digite um número válido.")

@log_transacao
def criar_cliente(clientes):
    cpf = input("\nInforme seu CPF (Apenas números): ")
    cliente = filtrar_cliente(cpf, clientes)
    numero = ""
    pattern = r"^\([0-9]{2}\) [9][0-9]{4}\-[0-9]{4}$"

    if cliente:
        print("\n Já existe um usuário cadastrado com este CPF!")
        return

    nome = input("\nInforme seu nome completo: ")
    data_nascimento = input("\nInforme sua data de nascimento (dd/mm/aaaa): ")
    print(
        """\n
        =======================================
        Agora, informe os dados do seu endereço:
        =======================================
        \n""")
    cep = input("\nInforme seu CEP: ")
    logradouro = input("\nInforme o nome da rua/avenida/travessa: ")
    telefone = validate(numero, pattern)
    complemento = input("\nInforme o complemento (ex: Casa/Apartamento): ")
    bairro = input("\nInforme o bairro: ")
    cidade = input("\nInforme a cidade: ")
    estado = input("\nInforme o estado: ")

    cliente = PessoaFisica(nome=nome, cpf=cpf, data_nascimento=data_nascimento, cep=cep,
                        logradouro=logradouro, telefone=telefone,
                        complemento=complemento, bairro=bairro, cidade=cidade,
                        estado=estado)

    clientes.append(cliente)

    print(
        """\n
        ==============  ===============
        Cliente cadastrado com sucesso!
        ==============  ===============
        """)

    print(clientes)


def filtrar_usuario(cpf, usuarios):
    usuarios_filtrados = [usuario for usuario in usuarios if usuario["cpf"] == cpf]
    return usuarios_filtrados[0] if usuarios_filtrados else None


@log_transacao
def criar_conta(numero_conta, clientes, contas):
    cpf = input("\nInforme seu CPF (apenas números): ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n Não há um cadastro para este CPF.\n")
        return

    conta = ContaCorrente.nova_conta(cliente=cliente, numero=numero_conta)
    contas.append(conta)
    cliente.contas.append(conta)

    print("\nConta cadastrada com sucesso.")


def listar_contas(contas):
    for conta in contas:
        print("=" * 100)
        print(textwrap.dedent(str(conta)))


def main():
    clientes = []
    contas = []

    while True:
        opcao = menu()

        if opcao == "1":
            depositar(clientes)

        elif opcao == "2":
            sacar(clientes)

        elif opcao == "3":
            exibir_extrato(clientes)

        elif opcao == "4":
            numero_conta = len(contas) + 1
            criar_conta(numero_conta, clientes, contas)

        elif opcao == "5":
            criar_cliente(clientes)

        elif opcao == "6":
            listar_contas(contas)

        elif opcao == "0":
            break

        else:
            print("\nPor favor, selecione uma das opções.\n")


main()
