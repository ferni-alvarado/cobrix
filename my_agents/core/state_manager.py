import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class StateManager:
    """
    Gestor centralizado del estado de conversaciones y pedidos.
    Implementa el patrón Singleton para acceso global.
    """

    _instance = None
    _conversation_states: Dict[str, Dict] = {}
    _preference_mapping: Dict[str, str] = {}  # Mapeo entre preference_id y user_id
    _order_mapping: Dict[str, str] = {}  # Mapeo entre order_id y user_id
    _data_dir = Path("data/state")

    def __new__(cls):
        """Implementación del patrón Singleton"""
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance._load_state()
        return cls._instance

    @classmethod
    def get_instance(cls):
        """Obtiene la instancia única del StateManager"""
        if cls._instance is None:
            cls._instance = StateManager()
        return cls._instance

    def _load_state(self):
        """Carga el estado desde archivos persistentes"""
        # Crear directorio si no existe
        self._data_dir.mkdir(parents=True, exist_ok=True)

        # Cargar estados de conversación
        state_file = self._data_dir / "conversation_states.json"
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    self._conversation_states = json.load(f)
                print(
                    f"🔄 Estados de conversación cargados: {len(self._conversation_states)} conversaciones"
                )
            except Exception as e:
                print(f"⚠️ Error cargando estados de conversación: {e}")

        # Cargar mapeos de IDs
        mapping_file = self._data_dir / "id_mappings.json"
        if mapping_file.exists():
            try:
                with open(mapping_file, "r", encoding="utf-8") as f:
                    mappings = json.load(f)
                    self._preference_mapping = mappings.get("preference_mapping", {})
                    self._order_mapping = mappings.get("order_mapping", {})
                print(
                    f"🔄 Mapeos cargados: {len(self._preference_mapping)} preferencias, {len(self._order_mapping)} órdenes"
                )
            except Exception as e:
                print(f"⚠️ Error cargando mapeos de IDs: {e}")

    def _save_state(self):
        """Guarda el estado en archivos persistentes"""
        # Guardar estados de conversación
        state_file = self._data_dir / "conversation_states.json"
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(self._conversation_states, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error guardando estados de conversación: {e}")

        # Guardar mapeos de IDs
        mapping_file = self._data_dir / "id_mappings.json"
        try:
            mappings = {
                "preference_mapping": self._preference_mapping,
                "order_mapping": self._order_mapping,
            }
            with open(mapping_file, "w", encoding="utf-8") as f:
                json.dump(mappings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error guardando mapeos de IDs: {e}")

    def get_state(self, user_id: str) -> Dict:
        """Obtiene el estado de conversación para un usuario"""
        if user_id not in self._conversation_states:
            # Inicializar estado para nuevo usuario
            self._conversation_states[user_id] = {
                "context": "initial",
                "pending_order": None,
                "order_history": [],
                "waiting_for_alternative": False,
                "history": [],
                "last_updated": datetime.now().isoformat(),
            }
            self._save_state()

        return self._conversation_states[user_id]

    def update_state(self, user_id: str, state: Dict):
        """Actualiza el estado de conversación de un usuario"""
        self._conversation_states[user_id] = state
        state["last_updated"] = datetime.now().isoformat()
        self._save_state()

    def register_order(self, user_id: str, order_id: str, preference_id: str = None):
        """Registra un nuevo pedido y sus asociaciones"""
        # Actualizar mapeos
        self._order_mapping[order_id] = user_id
        if preference_id:
            self._preference_mapping[preference_id] = user_id

        # Guardar cambios
        self._save_state()

    def update_payment_status(
        self, preference_id: str, status: str, metadata: Optional[Dict] = None
    ) -> bool:
        """
        Actualiza el estado de pago para un pedido identificado por preference_id.

        Args:
            preference_id: ID de preferencia de Mercado Pago
            status: Nuevo estado (approved, pending, rejected, etc.)
            metadata: Información adicional sobre el pago

        Returns:
            bool: True si se actualizó correctamente, False si no se encontró
        """
        # Buscar el user_id asociado con este preference_id
        user_id = self._preference_mapping.get(preference_id)
        if not user_id:
            print(f"⚠️ No se encontró usuario para preference_id: {preference_id}")
            return False

        # Obtener el estado actual del usuario
        state = self._conversation_states.get(user_id, {})
        pending_order = state.get("pending_order", {})

        # Verificar que el pedido existe y coincide
        if not pending_order or pending_order.get("preference_id") != preference_id:
            print(
                f"⚠️ No se encontró un pedido pendiente con preference_id: {preference_id}"
            )
            return False

        # Actualizar el estado del pedido
        pending_order["status"] = status
        pending_order["payment_updated_at"] = datetime.now().isoformat()

        # Añadir metadatos si fueron proporcionados
        if metadata:
            if not pending_order.get("payment_metadata"):
                pending_order["payment_metadata"] = {}
            pending_order["payment_metadata"].update(metadata)

        # Marcar que debe notificar en la próxima interacción
        state["should_notify_payment"] = True
        state["notification_message"] = self._get_payment_notification_message(status)

        # Guardar en el historial si está aprobado
        if status == "approved" and not any(
            order.get("order_id") == pending_order.get("order_id")
            for order in state.get("order_history", [])
        ):
            if not state.get("order_history"):
                state["order_history"] = []

            # Crear copia del pedido para el historial
            order_copy = pending_order.copy()
            order_copy["completed_at"] = datetime.now().isoformat()
            state["order_history"].append(order_copy)

        # Actualizar el estado y guardar
        self._conversation_states[user_id] = state
        self._save_state()
        return True

    def _get_payment_notification_message(self, status: str) -> str:
        """Genera un mensaje de notificación basado en el estado del pago"""
        if status == "approved":
            return "¡Buenas noticias! Tu pago ha sido confirmado. Tu pedido está siendo preparado y pronto estará listo."
        elif status == "rejected":
            return "Lamentablemente, tu pago ha sido rechazado. Por favor, intenta con otro método de pago o contáctanos para asistencia."
        elif status == "pending":
            return "Tu pago está siendo procesado. Te notificaremos cuando se confirme."
        else:
            return f"El estado de tu pago ha cambiado a: {status}. Si tienes dudas, no dudes en consultarnos."

    def find_user_by_order_id(self, order_id: str) -> Optional[str]:
        """Busca el user_id asociado a un order_id"""
        return self._order_mapping.get(order_id)

    def find_user_by_preference_id(self, preference_id: str) -> Optional[str]:
        """Busca el user_id asociado a un preference_id"""
        return self._preference_mapping.get(preference_id)

    def find_order_by_id(self, order_id: str) -> Optional[Dict]:
        """Busca un pedido por su ID"""
        user_id = self._order_mapping.get(order_id)
        if not user_id:
            return None

        state = self._conversation_states.get(user_id, {})

        # Verificar pedido pendiente actual
        pending = state.get("pending_order", {})
        if pending and pending.get("order_id") == order_id:
            return pending

        # Buscar en historial
        for order in state.get("order_history", []):
            if order.get("order_id") == order_id:
                return order

        return None

    # Agregar este método al StateManager (paste-3.txt)

    def update_payment_status_by_order_id(
        self, order_id: str, status: str, metadata: Optional[Dict] = None
    ) -> bool:
        """
        Actualiza el estado de pago para un pedido identificado por order_id.

        Args:
            order_id: ID de la orden
            status: Nuevo estado (approved, pending, rejected, etc.)
            metadata: Información adicional sobre el pago

        Returns:
            bool: True si se actualizó correctamente, False si no se encontró
        """
        # Buscar el user_id asociado con este order_id
        user_id = self._order_mapping.get(order_id)
        if not user_id:
            print(f"⚠️ No se encontró usuario para order_id: {order_id}")
            return False

        # Obtener el estado actual del usuario
        state = self._conversation_states.get(user_id, {})
        pending_order = state.get("pending_order", {})

        # Verificar que el pedido existe y coincide
        if not pending_order or pending_order.get("order_id") != order_id:
            print(f"⚠️ No se encontró un pedido pendiente con order_id: {order_id}")
            return False

        # Actualizar el estado del pedido
        pending_order["status"] = status
        pending_order["payment_updated_at"] = datetime.now().isoformat()

        # Añadir metadatos si fueron proporcionados
        if metadata:
            if not pending_order.get("payment_metadata"):
                pending_order["payment_metadata"] = {}
            pending_order["payment_metadata"].update(metadata)

        # Marcar que debe notificar en la próxima interacción
        state["should_notify_payment"] = True
        state["notification_message"] = self._get_payment_notification_message(status)

        # Guardar en el historial si está aprobado
        if status == "approved" and not any(
            order.get("order_id") == pending_order.get("order_id")
            for order in state.get("order_history", [])
        ):
            if not state.get("order_history"):
                state["order_history"] = []

            # Crear copia del pedido para el historial
            order_copy = pending_order.copy()
            order_copy["completed_at"] = datetime.now().isoformat()
            state["order_history"].append(order_copy)

        # Actualizar el estado y guardar
        self._conversation_states[user_id] = state
        self._save_state()
        return True

    def get_all_states(self) -> Dict[str, Dict]:
        """
        Retorna una copia del diccionario de estados de conversación
        para todos los usuarios.
        """
        return self._conversation_states.copy()
