import asyncio
import logging

from my_agents.core.state_manager_json import JSONStateManager

from ..order_processing.payment_coordinator import PaymentCoordinator

CHECK_INTERVAL = 5  # segundos para test rápido

# Setup básico de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")


async def send_message(user_id: str, message: str):
    logging.info(f"Intentando enviar mensaje a {user_id}")
    # Simulación: loggear o imprimir. Cambiar esto por integración real (WhatsApp, Twilio, WebSocket, etc)
    logging.info(f"Mensaje enviado a {user_id}: {message}")
    print(f"[ENVIADO A {user_id}]: {message}")


async def payment_notifier_loop():
    logging.info("Iniciando payment_notifier_loop")
    state_manager = JSONStateManager.get_instance()
    payment_coordinator = PaymentCoordinator()

    while True:
        all_states = state_manager.get_all_states()
        notified_any = False

        logging.debug(
            f"🔍 Obteniendo todos los estados del JSONStateManager: {all_states}"
        )

        for user_id, state in all_states.items():
            logging.debug(f"🔵 Revisando estado para usuario {user_id}: {state}")
            if state.get("should_notify_payment"):
                notified_any = True
                order_details = state.get("pending_order", {})
                message = payment_coordinator.build_payment_confirmation(order_details)
                logging.info(f"📤 Enviando notificación de pago a {user_id}")
                await send_message(user_id, message)
                state["should_notify_payment"] = False
                state_manager.update_state(user_id, state)
                logging.info(
                    f"✅ Estado actualizado para {user_id}, should_notify_payment seteado a False"
                )

        # if not notified_any:
        #    logging.info("No hay pagos pendientes para notificar en este ciclo")

        await asyncio.sleep(CHECK_INTERVAL)
