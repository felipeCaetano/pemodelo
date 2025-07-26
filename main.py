from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QPushButton, QVBoxLayout, QWidget, QGraphicsTextItem, QGraphicsEllipseItem, 
    QGraphicsLineItem, QLineEdit
)
from PySide6.QtCore import QRectF, Qt, QPointF, QLineF, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPen, QPainter


class AtributoItem(QGraphicsEllipseItem):
    def __init__(self, nome, x, y, entidade):
        super().__init__(-10, -10, 20, 20)  # bolinha de raio 10
        self.setPen(QPen(Qt.black, 1.5))
        self.setBrush(QBrush(QColor("#FFFFFF")))
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)
        self.texto = QGraphicsTextItem(nome)
        self.texto.setFont(QFont("Arial", 8))
        self.texto.setDefaultTextColor(Qt.black)
        self.texto.setParentItem(self)
        self.texto.setPos(12, -8)
        self.entidade = entidade
        self.nome = nome
        self.x = x
        self.y = y
        self.unico = False  # Flag de atributo único
        self.ligacao = QGraphicsLineItem(self)
        self.atualizar_ligacao()
        self.setZValue(1)
        
        # Adiciona o atributo à cena primeiro, e só depois atualiza a linha
        QTimer.singleShot(0, self.atualizar_ligacao)

    def atualizar_ligacao(self):
        origem = self.mapToScene(QPointF(0, 0))  # centro da bolinha
        ent_rect = self.entidade.rect()
        destino = self.entidade.mapToScene(QPointF(ent_rect.width() / 2, ent_rect.height()))  # centro da base

        linha = QLineF(origem, destino)

        if not self.ligacao.scene():
            self.entidade.scene().addItem(self.ligacao)
        self.ligacao.setLine(linha)
        self.ligacao.setPen(QPen(Qt.black, 1))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.unico = not self.unico
            if self.unico:
                self.setBrush(QBrush(Qt.black))
            else:
                self.setBrush(QBrush(Qt.white))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.atualizar_ligacao()


class EntidadeItem(QGraphicsRectItem):
    def __init__(self, nome="Entidade", x=0, y=0, largura=120, altura=60):
        super().__init__(QRectF(0, 0, largura, altura))
        self.setBrush(QBrush(QColor("#E0E0E0")))
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemIsMovable)

        self.setPos(x, y)
        self.nome = nome
        self.texto = QGraphicsTextItem(self.nome, self)
        self.texto.setFont(QFont("Arial", 10))
        self.texto.setDefaultTextColor(Qt.black)
        self.centralizar_texto()
        self.atributos = []

    def centralizar_texto(self):
        rect = self.rect()
        text_rect = self.texto.boundingRect()
        x = (rect.width() - text_rect.width()) / 2
        y = (rect.height() - text_rect.height()) / 2
        self.texto.setPos(x, y)

    def adicionar_atributo(self, nome, posicao):
        atributo = AtributoItem(nome, posicao.x(), posicao.y(), self)
        atributo.setPos(posicao)
        self.scene().addItem(atributo)
        self.atributos.append(atributo)

    def mouseDoubleClickEvent(self, event):
        self.scene().parent().iniciar_edicao_nome(self)
        super().mouseDoubleClickEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.scene().parent().entidade_selecionada = self  # Marca como selecionada
        super().mousePressEvent(event)

    def atualizar_nome(self, novo_nome):
        self.nome = novo_nome
        self.texto.setPlainText(novo_nome)
        self.centralizar_texto()


class AreaGrafica(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene())
        self.scene().setParent(self)
        self.setRenderHint(QPainter.Antialiasing)
        self.setSceneRect(0, 0, 800, 600)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.editor_nome = None
        self.entidade_selecionada = None

    def adicionar_entidade(self, posicao: QPointF):
        entidade = EntidadeItem("Nova Entidade", posicao.x(), posicao.y())
        self.scene().addItem(entidade)
        self.entidade_selecionada = entidade

    def adicionar_atributo(self):
        if not self.entidade_selecionada:
            return
        pos = self.entidade_selecionada.scenePos() + QPointF(60, 100)
        nome = f"atributo{len(self.entidade_selecionada.atributos) + 1}"
        self.entidade_selecionada.adicionar_atributo(nome, pos)

    def iniciar_edicao_nome(self, entidade: EntidadeItem):
        if self.editor_nome:
            self.editor_nome.deleteLater()

        self.entidade_selecionada = entidade
        self.editor_nome = QLineEdit(entidade.nome, self)
        self.editor_nome.setFixedWidth(int(entidade.rect().width()))
        ponto = self.mapFromScene(entidade.scenePos())
        self.editor_nome.move(ponto)
        self.editor_nome.setFocus()
        self.editor_nome.returnPressed.connect(lambda: self.finalizar_edicao_nome(entidade))
        self.editor_nome.editingFinished.connect(lambda: self.finalizar_edicao_nome(entidade))
        self.editor_nome.show()

    def finalizar_edicao_nome(self, entidade: EntidadeItem):
        if not self.editor_nome:
            return
        novo_nome = self.editor_nome.text()
        entidade.atualizar_nome(novo_nome)
        self.editor_nome.deleteLater()
        self.editor_nome = None


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BRModelo Clone - Atributos com Ligação")
        self.setGeometry(100, 100, 1000, 700)

        self.area_grafica = AreaGrafica()
        self.botao_entidade = QPushButton("Nova Entidade")
        self.botao_entidade.clicked.connect(self.criar_entidade)

        self.botao_atributo = QPushButton("Adicionar Atributo")
        self.botao_atributo.clicked.connect(self.area_grafica.adicionar_atributo)

        layout = QVBoxLayout()
        layout.addWidget(self.botao_entidade)
        layout.addWidget(self.botao_atributo)
        layout.addWidget(self.area_grafica)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def criar_entidade(self):
        centro = self.area_grafica.mapToScene(self.area_grafica.viewport().rect().center())
        self.area_grafica.adicionar_entidade(centro)


if __name__ == "__main__":
    app = QApplication([])
    janela = JanelaPrincipal()
    janela.show()
    app.exec()
