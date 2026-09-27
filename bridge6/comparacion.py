import json

def comparar_json(fichero1, fichero2):
    with open(fichero1, encoding="utf-8") as f:
        a = json.load(f)

    with open(fichero2, encoding="utf-8") as f:
        b = json.load(f)

    def comparar(a, b, ruta=""):
        if type(a) != type(b):
            print(f"{ruta}: tipo {type(a).__name__} != {type(b).__name__}")
            return

        if isinstance(a, dict):
            for clave in a.keys() | b.keys():
                nueva_ruta = f"{ruta}.{clave}" if ruta else clave

                if clave not in a:
                    print(f"{nueva_ruta}: SOLO EN FICHERO 2")
                elif clave not in b:
                    print(f"{nueva_ruta}: SOLO EN FICHERO 1")
                else:
                    comparar(a[clave], b[clave], nueva_ruta)

        elif isinstance(a, list):
            if len(a) != len(b):
                print(f"{ruta}: longitud {len(a)} != {len(b)}")

            for i, (x, y) in enumerate(zip(a, b)):
                comparar(x, y, f"{ruta}[{i}]")

        elif a != b:
            print(f"{ruta}: {a!r} != {b!r}")

    comparar(a, b)


if __name__ == "__main__":
    comparar_json(
        "/home/pepe/Desarrollo/música/bridge6/bridge6_modificado.malo.json",
        "/home/pepe/Desarrollo/música/bridge6/Controlador_V2_2026-09-26_23-46-05.json"
    )
