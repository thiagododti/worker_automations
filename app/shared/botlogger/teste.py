from botlogger import Botlogger
from datetime import datetime,timedelta

def teste_manual():
    etapas = [
        {   
            "etapa": "etapa1",
            "date_start": datetime.now().isoformat(),
            "date_end": (datetime.now() + timedelta(minutes=1)).isoformat(),
            "status": "concluido"},
        {
            "etapa": "etapa2",
            "date_start": datetime.now().isoformat(),
            "date_end": (datetime.now() + timedelta(minutes=1)).isoformat(),
            "status": "erro"
        },
        {
            "etapa": "etapa3",
            "date_start": datetime.now().isoformat(),
            "date_end": (datetime.now() + timedelta(minutes=1)).isoformat(),
            "status": "alerta"
        },
        {
            "etapa": "etapa4",
            "date_start": datetime.now().isoformat(),
            "date_end": None,
            "status": "erro"
        }
    ]

    botlogger = Botlogger("08880518000179", envio_manual=True)
    botlogger.inicio_execucao(date_start=datetime.now().isoformat(), date_end=(datetime.now() + timedelta(minutes=len(etapas))).isoformat(), status="concluido")
    for item in etapas:
        try:
            botlogger.inicio_etapa(identificacao=item["etapa"], date_start=item["date_start"], date_end=item["date_end"], status=item["status"])
        except Exception as e:
            print(f"Erro ao enviar etapa {item['etapa']}: {e}")
    

if __name__ == "__main__":
    teste_manual()