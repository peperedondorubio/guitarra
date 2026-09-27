import json
import copy
from pathlib import Path
import secrets
import sys
import shutil

def obtener_fichero_json():
    if len(sys.argv) != 2:
        raise ValueError(
            "Uso: python main.py <fichero.json>"
        )

    fichero = Path(sys.argv[1]).expanduser().resolve()

    if not fichero.exists():
        raise FileNotFoundError(
            f"No existe el fichero: {fichero}"
        )

    if fichero.suffix.lower() != ".json":
        raise ValueError(
            f"El fichero debe tener extensión .json: {fichero}"
        )

    return fichero



def cargar_configuracion(fichero):
    with fichero.open("r", encoding="utf-8") as f:
        return json.load(f)

def crear_copia_seguridad(fichero):
    backup = fichero.with_name(
        f"{fichero.stem}_backup{fichero.suffix}"
    )

    shutil.copy2(fichero, backup)

    print()
    print("Copia de seguridad creada:")
    print(backup)

    return backup


def mostrar_estructura(config, salida):
    """
    Añade a 'salida' la estructura de bancos y setlists.
    No modifica la configuración.
    """

    bank_settings = config["bankSettings"]
    set_lists = config["globalSettings"]["setLists"]

    def escribir(texto=""):
        salida.append(texto)
        print(texto)

    # ------------------------------------------------------------------
    # SETLISTS
    # ------------------------------------------------------------------

    escribir()
    escribir("SETLISTS")
    escribir("=" * 80)

    for setlist in set_lists:
        nombre = setlist.get("name", "") or "(SIN NOMBRE)"
        items = setlist.get("items", [])

        escribir()
        escribir(f"Nombre de la Set List: {nombre}")

        canciones = []
        indices_validos = True

        for bank_index in items:
            if 0 <= bank_index < len(bank_settings):
                bank_name = bank_settings[bank_index].get(
                    "bankName", ""
                ) or "(SIN NOMBRE)"
                canciones.append(bank_name)
            else:
                canciones.append(f"(BANCO INVALIDO: {bank_index})")
                indices_validos = False

        if not items:
            escribir("Nuevo orden de canciones: (vacío)")
        else:
            escribir(
                "Nuevo orden de canciones (separadas por coma):"
            )
            escribir(", ".join(canciones))

        if not indices_validos:
            escribir("  AVISO: la Set List contiene índices de banco inválidos.")

    # ------------------------------------------------------------------
    # BANCOS
    # ------------------------------------------------------------------

    escribir()
    escribir()
    escribir("=" * 80)
    escribir("BANCOS")
    escribir("=" * 80)

    for index, banco in enumerate(bank_settings):

        nombre = banco.get("bankName", "") or "(SIN NOMBRE)"

        escribir(
            f"{index:3}  {nombre}"
        )


def analizar_contenido_mensajes(config):
    """
    Analiza cuántos mensajes reales contiene cada tipo de mensaje
    en primary y secondary.
    """
    bancos = config["bankSettings"]

    campos = [
        "toggleOnMessages",
        "toggleOffMessages",
        "pressMessages",
        "releaseMessages",
        "doublePressMessages",
        "holdMessages",
        "holdReleaseMessages",
        "secondaryToggleOnMessages",
        "secondaryToggleOffMessages",
    ]

    totales = {campo: 0 for campo in campos}
    pulsadores_con_mensajes = {campo: 0 for campo in campos}

    for banco in bancos:
        for pulsador in banco.get("footswitches", []):
            for campo in campos:
                bloque = pulsador.get(campo, {})
                mensajes = bloque.get("messages", [])
                cantidad = len(mensajes)

                if cantidad > 0:
                    pulsadores_con_mensajes[campo] += 1
                    totales[campo] += cantidad

    print()
    print("=" * 80)
    print("CONTENIDO REAL DE LOS MENSAJES")
    print("=" * 80)

    for campo in campos:
        print(
            f"{campo:<30} "
            f"pulsadores={pulsadores_con_mensajes[campo]:4} "
            f"mensajes={totales[campo]:5}"
        )


def analizar_pulsadores(config):
    """
    Analiza qué tipos de mensajes se utilizan realmente
    en primary y secondary de todos los bancos.
    """

    bancos = config["bankSettings"]

    campos_primary = [
        "toggleOnMessages",
        "toggleOffMessages",
        "pressMessages",
        "releaseMessages",
        "doublePressMessages",
        "holdMessages",
        "holdReleaseMessages",
    ]

    campos_secondary = [
        "secondaryToggleOnMessages",
        "secondaryToggleOffMessages",
    ]

    print()
    print("=" * 80)
    print("ANÁLISIS DE PULSADORES")
    print("=" * 80)

    usos_primary = {campo: 0 for campo in campos_primary}
    usos_secondary = {campo: 0 for campo in campos_secondary}

    casos_primary_complejos = []

    for bank_index, banco in enumerate(bancos):

        bank_name = banco.get("bankName", "") or "(SIN NOMBRE)"

        for switch_index, pulsador in enumerate(
            banco.get("footswitches", [])
        ):

            nombre = (
                pulsador.get("name", "")
                or f"Pulsador {switch_index + 1}"
            )

            # ------------------------------------------------------
            # PRIMARY
            # ------------------------------------------------------

            usados_primary = []

            for campo in campos_primary:
                bloque = pulsador.get(campo, {})
                mensajes = bloque.get("messages", [])

                if mensajes:
                    usos_primary[campo] += 1
                    usados_primary.append(campo)

            if any(
                campo in usados_primary
                for campo in [
                    "pressMessages",
                    "releaseMessages",
                    "doublePressMessages",
                    "holdMessages",
                    "holdReleaseMessages",
                ]
            ):
                casos_primary_complejos.append(
                    (
                        bank_index,
                        bank_name,
                        switch_index,
                        nombre,
                        usados_primary,
                    )
                )

            # ------------------------------------------------------
            # SECONDARY
            # ------------------------------------------------------

            for campo in campos_secondary:
                bloque = pulsador.get(campo, {})
                mensajes = bloque.get("messages", [])

                if mensajes:
                    usos_secondary[campo] += 1

    # --------------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------------

    print()
    print("USO DE MENSAJES PRIMARY")
    print("-" * 80)

    for campo, cantidad in usos_primary.items():
        print(f"{campo:<30} {cantidad:4}")

    print()
    print("USO DE MENSAJES SECONDARY")
    print("-" * 80)

    for campo, cantidad in usos_secondary.items():
        print(f"{campo:<30} {cantidad:4}")

    # --------------------------------------------------------------
    # CASOS POTENCIALMENTE PROBLEMÁTICOS
    # --------------------------------------------------------------

    print()
    print("=" * 80)
    print("PRIMARY CON MENSAJES SIN EQUIVALENTE SECONDARY")
    print("=" * 80)

    if not casos_primary_complejos:
        print("NINGUNO")
    else:
        for (
            bank_index,
            bank_name,
            switch_index,
            nombre,
            campos,
        ) in casos_primary_complejos:

            print()
            print(f"Banco {bank_index}: {bank_name}")
            print(
                f"  Pulsador {switch_index + 1}: {nombre}"
            )
            print(
                f"  Campos: {', '.join(campos)}"
            )

def reordenar_setlist(config, nombre_setlist, nuevo_orden):
    """
    Reordena los bancos de un setlist según los nombres indicados.

    nuevo_orden debe contener exactamente los nombres de las canciones
    que forman parte del setlist, en el orden deseado.
    """

    bancos = config["bankSettings"]
    setlists = config["globalSettings"]["setLists"]

    # ---------------------------------------------------------
    # Buscar el setlist
    # ---------------------------------------------------------

    setlist_encontrado = None

    for setlist in setlists:
        if setlist.get("name") == nombre_setlist:
            setlist_encontrado = setlist
            break

    if setlist_encontrado is None:
        raise ValueError(
            f"No se ha encontrado el setlist: {nombre_setlist!r}"
        )

    # ---------------------------------------------------------
    # Obtener los bancos que realmente pertenecen al setlist
    # ---------------------------------------------------------

    indices_actuales = list(
        setlist_encontrado.get("items", [])
    )

    # Comprobar que los índices son válidos
    for index in indices_actuales:
        if not isinstance(index, int) or index < 0 or index >= len(bancos):
            raise ValueError(
                f"El setlist {nombre_setlist!r} contiene "
                f"un índice de banco inválido: {index!r}"
            )

    # ---------------------------------------------------------
    # Crear mapa nombre -> índice SOLO para los bancos
    # pertenecientes al setlist
    # ---------------------------------------------------------

    bancos_por_nombre = {}

    for index in indices_actuales:
        banco = bancos[index]
        nombre = banco.get("bankName")

        if nombre in bancos_por_nombre:
            raise ValueError(
                f"Hay bancos con nombre duplicado dentro del setlist "
                f"{nombre_setlist!r}: {nombre!r}"
            )

        bancos_por_nombre[nombre] = index

    # ---------------------------------------------------------
    # Comprobar que nuevo_orden no contiene nombres duplicados
    # ---------------------------------------------------------

    if len(nuevo_orden) != len(set(nuevo_orden)):
        raise ValueError(
            "El nuevo orden contiene canciones/bancos duplicados."
        )

    # ---------------------------------------------------------
    # Comprobar que todas las canciones existen en el setlist
    # ---------------------------------------------------------

    indices_nuevos = []

    for nombre in nuevo_orden:

        if nombre not in bancos_por_nombre:
            raise ValueError(
                f"La canción/banco {nombre!r} no pertenece "
                f"al setlist {nombre_setlist!r}"
            )

        indices_nuevos.append(
            bancos_por_nombre[nombre]
        )

    # ---------------------------------------------------------
    # Comprobar que están exactamente todas las canciones
    # actuales
    # ---------------------------------------------------------

    if set(indices_actuales) != set(indices_nuevos):
        raise ValueError(
            f"El nuevo orden no contiene exactamente las canciones "
            f"actuales del setlist {nombre_setlist!r}"
        )

    # ---------------------------------------------------------
    # Guardar el orden anterior
    # ---------------------------------------------------------

    orden_anterior = list(indices_actuales)

    # ---------------------------------------------------------
    # Aplicar nuevo orden
    # ---------------------------------------------------------

    setlist_encontrado["items"] = indices_nuevos
    setlist_encontrado["size"] = len(indices_nuevos)

    # ---------------------------------------------------------
    # Mostrar resultado
    # ---------------------------------------------------------

    print()
    print(f"Setlist reordenado: {nombre_setlist}")
    print()

    print("Orden anterior:")

    for posicion, index in enumerate(orden_anterior, start=1):
        print(
            f"  {posicion:2}. "
            f"{bancos[index].get('bankName')}"
        )

    print()

    print("Nuevo orden:")

    for posicion, index in enumerate(indices_nuevos, start=1):
        print(
            f"  {posicion:2}. "
            f"{bancos[index].get('bankName')}"
        )

    return orden_anterior


def generar_bank_id_unico(config):
    """
    Genera un bankId positivo que no esté utilizado por ningún banco
    de la configuración.
    """
    usados = {
        banco.get("bankId")
        for banco in config.get("bankSettings", [])
        if banco.get("bankId") is not None
    }

    while True:
        candidato = secrets.randbelow(2**31 - 1) + 1
        if candidato not in usados:
            return candidato


def asignar_bank_ids_aleatorios(config):
    """
    Asigna un bankId nuevo y único a todos los bancos.

    Los bankName permanecen intactos.
    """

    for banco in config.get("bankSettings", []):
        banco["bankId"] = generar_bank_id_unico(config)


def cambiar_tempo(config, nombre_cancion, nuevo_tempo):
    for banco in config["bankSettings"]:

        if banco.get("bankName") != nombre_cancion:
            continue

        # Clock 0 y clock 1
        midi_clocks = banco["midiClocks"]

        anteriores = [c["tempo"] for c in midi_clocks]

        midi_clocks[0]["tempo"] = nuevo_tempo
        midi_clocks[1]["tempo"] = nuevo_tempo

        # Buscar específicamente el pulsador asociado al clock 0
        for footswitch in banco["footswitches"]:
            if (
                footswitch.get("primaryMode") == "tapTempo"
                and footswitch.get("midiClock") == 0
            ):
                footswitch["name"] = f"A:{nuevo_tempo:.1f}"
                break
        else:
            raise ValueError(
                f"No se encontró el pulsador tapTempo del clock 0 "
                f"en {nombre_cancion!r}"
            )

     # Asignar un bankId nuevo, no utilizado en esta configuración.
        # La prueba realizada indica que un identificador nuevo permite
        # que Bridge6 reconozca los cambios.
        bank_id_anterior = banco.get("bankId")
        banco["bankId"] = generar_bank_id_unico(config)
        print(
            f"{nombre_cancion}: "
            f"midiClocks {anteriores} -> "
            f"[{nuevo_tempo}, {nuevo_tempo}]"
        )
        print(
                f"bankId: {bank_id_anterior} -> {banco['bankId']}"
            )
        return anteriores

    raise ValueError(
        f"No se ha encontrado el banco/canción: {nombre_cancion!r}"
    )




def inspeccionar_pulsador(config, nombre_banco, nombre_pulsador):
    bancos = config["bankSettings"]

    banco = next(
        (
            b for b in bancos
            if b.get("bankName") == nombre_banco
        ),
        None
    )

    if banco is None:
        raise ValueError(f"No existe el banco: {nombre_banco}")

    pulsador = next(
        (
            p for p in banco.get("footswitches", [])
            if p.get("name") == nombre_pulsador
        ),
        None
    )

    if pulsador is None:
        raise ValueError(
            f"No existe el pulsador {nombre_pulsador!r} "
            f"en {nombre_banco!r}"
        )

    campos = [
        "primaryState",
        "secondaryState",
        "primaryMode",
        "secondaryMode",
        "primaryColor",
        "secondaryColor",
        "primaryLedMode",
        "secondaryLedMode",
        "toggleOnMessages",
        "toggleOffMessages",
        "pressMessages",
        "releaseMessages",
        "doublePressMessages",
        "holdMessages",
        "holdReleaseMessages",
        "secondaryToggleOnMessages",
        "secondaryToggleOffMessages",
    ]

    print()
    print("=" * 80)
    print(f"{nombre_banco} / {nombre_pulsador}")
    print("=" * 80)

    for campo in campos:
        print()
        print(f"--- {campo} ---")

        valor = pulsador.get(campo)

        print(json.dumps(
            valor,
            indent=2,
            ensure_ascii=False
        ))



def buscar_pulsadores_en_todos_los_bancos(
    config,
    indice1,
    indice2,
):
    """
    Localiza dos pulsadores por posición física en todos los bancos.

    No utiliza el nombre del pulsador, porque el nombre puede cambiar
    durante un swap.
    """

    bancos = config["bankSettings"]
    encontrados = []

    for bank_index, banco in enumerate(bancos):

        pulsadores = banco.get("footswitches", [])

        if indice1 >= len(pulsadores):
            raise ValueError(
                f"Banco {bank_index} ({banco.get('bankName')!r}): "
                f"no existe el pulsador {indice1}"
            )

        if indice2 >= len(pulsadores):
            raise ValueError(
                f"Banco {bank_index} ({banco.get('bankName')!r}): "
                f"no existe el pulsador {indice2}"
            )

        if indice1 == indice2:
            raise ValueError(
                f"Los pulsadores origen y destino son el mismo: "
                f"{indice1}"
            )

        encontrados.append(
            (
                bank_index,
                banco,
                pulsadores[indice1],
                pulsadores[indice2],
            )
        )

    return encontrados


def swap_pulsadores(
    config,
    pulsador1,
    lado1,
    pulsador2,
    lado2,
    nombre1,
    nombre2,
):
    """
    Intercambia los datos de los lados seleccionados de dos pulsadores.

    Los modos NO se intercambian:
        primaryMode   = "toggle"      (siempre)
        secondaryMode = "holdToggle"  (siempre)

    PRIMARY intercambia:
        primaryState
        primaryColor
        primaryLedMode
        toggleOnMessages

    SECONDARY intercambia:
        secondaryState
        secondaryColor
        secondaryLedMode
        holdReleaseMessages

    El resto de mensajes NO se modifica.
    """

    if lado1 not in ("primary", "secondary"):
        raise ValueError(
            f"Lado inválido para pulsador 1: {lado1!r}"
        )

    if lado2 not in ("primary", "secondary"):
        raise ValueError(
            f"Lado inválido para pulsador 2: {lado2!r}"
        )

    encontrados = buscar_pulsadores_en_todos_los_bancos(
        config,
        pulsador1,
        pulsador2,
    )

    for _, _, p1, p2 in encontrados:

        # ==========================================================
        # GUARDAR LOS VALORES ORIGINALES
        # ==========================================================

        if lado1 == "primary":
            state1 = copy.deepcopy(p1.get("primaryState"))
            color1 = copy.deepcopy(p1.get("primaryColor"))
            led1 = copy.deepcopy(p1.get("primaryLedMode"))
            mensajes1 = copy.deepcopy(
                p1.get("toggleOnMessages")
            )
        else:
            state1 = copy.deepcopy(p1.get("secondaryState"))
            color1 = copy.deepcopy(p1.get("secondaryColor"))
            led1 = copy.deepcopy(p1.get("secondaryLedMode"))
            mensajes1 = copy.deepcopy(
                p1.get("holdReleaseMessages")
            )

        if lado2 == "primary":
            state2 = copy.deepcopy(p2.get("primaryState"))
            color2 = copy.deepcopy(p2.get("primaryColor"))
            led2 = copy.deepcopy(p2.get("primaryLedMode"))
            mensajes2 = copy.deepcopy(
                p2.get("toggleOnMessages")
            )
        else:
            state2 = copy.deepcopy(p2.get("secondaryState"))
            color2 = copy.deepcopy(p2.get("secondaryColor"))
            led2 = copy.deepcopy(p2.get("secondaryLedMode"))
            mensajes2 = copy.deepcopy(
                p2.get("holdReleaseMessages")
            )

        # ==========================================================
        # ESCRIBIR PULSADOR 1
        # ==========================================================

        if lado1 == "primary":
            p1["primaryState"] = state2
            p1["primaryColor"] = color2
            p1["primaryLedMode"] = led2

            if mensajes2 is not None:
                p1["toggleOnMessages"] = mensajes2

        else:
            p1["secondaryState"] = state2
            p1["secondaryColor"] = color2
            p1["secondaryLedMode"] = led2

            if mensajes2 is not None:
                p1["holdReleaseMessages"] = mensajes2

        # ==========================================================
        # ESCRIBIR PULSADOR 2
        # ==========================================================

        if lado2 == "primary":
            p2["primaryState"] = state1
            p2["primaryColor"] = color1
            p2["primaryLedMode"] = led1

            if mensajes1 is not None:
                p2["toggleOnMessages"] = mensajes1

        else:
            p2["secondaryState"] = state1
            p2["secondaryColor"] = color1
            p2["secondaryLedMode"] = led1

            if mensajes1 is not None:
                p2["holdReleaseMessages"] = mensajes1

        # ==========================================================
        # ASEGURAR LOS MODOS FIJOS DE BRIDGE6
        # ==========================================================

        p1["primaryMode"] = "toggle"
        p1["secondaryMode"] = "holdToggle"

        p2["primaryMode"] = "toggle"
        p2["secondaryMode"] = "holdToggle"

        # ==========================================================
        # NOMBRES
        # ==========================================================

        p1["name"] = nombre1
        p2["name"] = nombre2


    asignar_bank_ids_aleatorios(config)

    print()
    print(
        f"{lado1.upper()} del pulsador {pulsador1 + 1}"
        f" ⇄ "
        f"{lado2.upper()} del pulsador {pulsador2 + 1}"
    )

    print(
        f"  Pulsador {pulsador1 + 1}: {nombre1}"
    )

    print(
        f"  Pulsador {pulsador2 + 1}: {nombre2}"
    )


def main():

    fichero = obtener_fichero_json()

    # La copia se hace sobre el JSON original antes de modificarlo.
    crear_copia_seguridad(fichero)

    config = cargar_configuracion(fichero)

    while True:
        print()
        print("=" * 50)
        print("      EDITOR DE CONFIGURACIÓN BRIDGE6")
        print("=" * 50)
        print("1) Situación actual")
        print("2) Cambiar Set List")
        print("3) Cambiar tempo")
        print("4) Swap de pulsadores")
        print("0) Guardar y salir")
        print("=" * 50)

        opcion = input("Opción: ").strip()

        # --------------------------------------------------------
        # 1. SITUACIÓN ACTUAL
        # --------------------------------------------------------
        if opcion == "1":
            mostrar_estructura(config, [])

        # --------------------------------------------------------
        # 2. CAMBIAR SET LIST
        # --------------------------------------------------------
        elif opcion == "2":
            print()
            print("Set Lists disponibles:")

            for setlist in config["globalSettings"]["setLists"]:
                print(f"  - {setlist['name']}")

            nombre_setlist = input(
                "\nNombre de la Set List: "
            ).strip()

            nuevo_orden = input(
                "Nuevo orden de canciones (separadas por coma):\n"
            ).strip()

            nuevo_orden = [
                nombre.strip()
                for nombre in nuevo_orden.split(",")
                if nombre.strip()
            ]

            reordenar_setlist(
                config,
                nombre_setlist,
                nuevo_orden,
            )

        # --------------------------------------------------------
        # 3. CAMBIAR TEMPO
        # --------------------------------------------------------
        elif opcion == "3":
            nombre_cancion = input(
                "\nNombre de la canción: "
            ).strip()

            nuevo_tempo = int(
                input("Nuevo tempo: ").strip()
            )

            cambiar_tempo(
                config,
                nombre_cancion,
                nuevo_tempo,
            )

        # --------------------------------------------------------
        # 4. SWAP PULSADORES
        # --------------------------------------------------------
        elif opcion == "4":

            print()
            print("=" * 50)
            print("              SWAP DE PULSADORES")
            print("=" * 50)

            pulsador1 = int(
                input("Pulsador 1 (1-6): ").strip()
            )

            if not 1 <= pulsador1 <= 6:
                raise ValueError(
                    "El pulsador debe estar entre 1 y 6"
                )

            lado1 = input(
                "Lado del pulsador 1 (p)rimary/(s)econdary: "
            ).strip().lower()

            if lado1 not in ("p", "s"):
                raise ValueError(
                    "El lado debe ser 'p' (primary) o 's' (secondary)"
                )

            lado1 = "primary" if lado1 == "p" else "secondary"

            pulsador2 = int(
                input("Pulsador 2 (1-6): ").strip()
            )

            if not 1 <= pulsador2 <= 6:
                raise ValueError(
                    "El pulsador debe estar entre 1 y 6"
                )

            if pulsador1 == pulsador2:
                raise ValueError(
                    "Los dos pulsadores deben ser diferentes"
                )

            lado2 = input(
                "Lado del pulsador 2 (p)rimary/(s)econdary: "
            ).strip().lower()

            if lado2 not in ("p", "s"):
                raise ValueError(
                    "El lado debe ser 'p' (primary) o 's' (secondary)"
                )

            lado2 = "primary" if lado2 == "p" else "secondary"

            nombre1 = input(
                f"Nombre final del pulsador {pulsador1}: "
            ).strip()

            nombre2 = input(
                f"Nombre final del pulsador {pulsador2}: "
            ).strip()

            # Convertimos 1-6 -> índices Python 0-5
            p1 = pulsador1 - 1
            p2 = pulsador2 - 1

            swap_pulsadores(
                config,
                pulsador1=p1,
                lado1=lado1,
                pulsador2=p2,
                lado2=lado2,
                nombre1=nombre1,
                nombre2=nombre2,
            )


        # --------------------------------------------------------
        # 0. GUARDAR Y SALIR
        # --------------------------------------------------------
        elif opcion == "0":

            with fichero.open("w", encoding="utf-8") as f:
                json.dump(
                    config,
                    f,
                    ensure_ascii=False,
                    separators=(",", ":")
                )

            print()
            print("Configuración guardada en:")
            print(fichero)
            break

        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()