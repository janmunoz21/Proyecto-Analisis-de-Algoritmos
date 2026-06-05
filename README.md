# Proyecto Análisis de Algoritmos
Proyecto de análisis de algoritmos 2025-3, Jan Marco Muñoz

# Diagramas Mermaid
# Procesamiento Distribuido de Imagenes en Redes P2P Moviles con Modelo de Recompensas
# Pontificia Universidad Javeriana — Mayo 2026

> **Nota sobre protocolo de comunicacion entre nodos:** El uso de gRPC sobre HTTP/2 como
> protocolo de comunicacion entre dispositivos esta planteado como opcion tecnologica pero es
> **sujeto a cambio** durante la fase de desarrollo. En los diagramas se referencia como
> *Canal P2P Local* y se anota con ⚠ donde corresponde.

---

## 1. Diagramas de Secuencia

---

### DS-01 · Registro de Usuario (CU-01)

```mermaid
sequenceDiagram
    actor U as Usuario
    participant APP as App Android
    participant API as Backend REST
    participant DB as Base de Datos Central

    U->>APP: Ingresa nombre, correo, contrasena y rol
    APP->>APP: Valida formato de los campos localmente
    alt Datos invalidos
        APP-->>U: Muestra errores de validacion en pantalla
    else Datos validos
        APP->>API: POST /auth/registro (nombre, correo, hash_password, rol)
        activate API
        API->>DB: INSERT INTO Usuario
        alt Correo ya registrado
            DB-->>API: Error de unicidad (duplicate key)
            API-->>APP: 409 Conflict
            deactivate API
            APP-->>U: El correo ya esta registrado
        else Registro exitoso
            DB-->>API: Usuario creado con UUID asignado
            API-->>APP: 201 Created - token JWT y perfil de usuario
            deactivate API
            APP->>APP: Almacena token JWT en memoria segura
            alt Rol = CONSUMIDOR
                APP-->>U: Redirige a Dashboard Consumidor
            else Rol = PROVEEDOR
                APP-->>U: Redirige a Dashboard Proveedor
            end
        end
    end
```

---

### DS-02 · Inicio de Sesion (CU-02)

```mermaid
sequenceDiagram
    actor U as Usuario
    participant APP as App Android
    participant API as Backend REST
    participant DB as Base de Datos Central

    U->>APP: Ingresa correo y contrasena
    APP->>API: POST /auth/login (correo, password)
    activate API
    API->>DB: SELECT Usuario WHERE correo = correo_ingresado
    DB-->>API: Registro con hash de contrasena y rol
    API->>API: Verifica hash de contrasena
    deactivate API
    alt Credenciales invalidas
        API-->>APP: 401 Unauthorized
        APP-->>U: Credenciales incorrectas - intente de nuevo
    else Credenciales validas
        API-->>APP: 200 OK - token JWT, perfil, rol y saldo
        APP->>APP: Guarda token en memoria volatil
        APP->>APP: Carga historial y datos de perfil del usuario
        alt Rol = CONSUMIDOR
            APP-->>U: Redirige a Dashboard Consumidor
        else Rol = PROVEEDOR
            APP-->>U: Redirige a Dashboard Proveedor
        end
    end
```

---

### DS-03 · Publicacion de Nodo Proveedor (CU-03)

```mermaid
sequenceDiagram
    actor P as Proveedor
    participant APP_P as App Proveedor
    participant BG as Background Service
    participant MDNS as mDNS Red WiFi Local

    P->>APP_P: Pulsa Activar modo colaborador
    APP_P->>BG: Inicia Android Service en segundo plano
    activate BG
    BG->>BG: Abre socket de escucha en puerto local
    Note over BG: Protocolo de aplicacion entre nodos sujeto a cambio
    BG->>MDNS: Anuncia servicio (IP local, puerto, nombre del nodo)
    MDNS-->>BG: Anuncio propagado exitosamente en la subred
    BG-->>APP_P: Estado del nodo actualizado a ACTIVO
    deactivate BG
    APP_P-->>P: Nodo publicado exitosamente en la red WiFi
    APP_P->>APP_P: UI muestra indicador de estado ACTIVO

    loop Escucha activa de tareas entrantes
        MDNS->>BG: Solicitud de procesamiento de consumidor
        activate BG
        BG->>BG: Deserializa tensor intermedio recibido
        BG->>BG: Ejecuta capas finales de MobileNetV3 con TFLite
        BG->>MDNS: Retorna resultado de clasificacion al consumidor
        deactivate BG
    end
```

---

### DS-04 · Descubrimiento y Conexion a Nodo Proveedor (CU-04)

```mermaid
sequenceDiagram
    actor C as Consumidor
    participant APP_C as App Consumidor
    participant MDNS as mDNS Red WiFi Local
    participant APP_P as App Proveedor

    C->>APP_C: Solicita buscar nodos disponibles en la red
    APP_C->>MDNS: Escaneo de servicios en subred local
    Note over APP_C,MDNS: Tiempo maximo de descubrimiento: 2500 ms
    MDNS->>APP_P: Query de descubrimiento (broadcast en subred)
    APP_P-->>MDNS: Responde con IP local, puerto y estado ACTIVO
    MDNS-->>APP_C: Lista de nodos proveedores encontrados
    APP_C->>APP_C: Filtra nodos con estado ACTIVO disponibles
    alt Nodos disponibles encontrados
        APP_C->>APP_P: Handshake de conexion (TLS v1.3)
        Note over APP_C,APP_P: Protocolo de aplicacion sobre TLS: sujeto a cambio
        APP_P-->>APP_C: Conexion establecida y cifrada correctamente
        APP_C-->>C: Lista de dispositivos conectados en pantalla
    else Sin nodos disponibles en la red
        APP_C-->>C: Sin nodos disponibles - se usara modo local
    end
```

---

### DS-05 · Inferencia Distribuida - Flujo Principal (CU-05, CU-06, CU-07)

```mermaid
sequenceDiagram
    actor C as Consumidor
    participant APP_C as App Consumidor
    participant TFL_C as TFLite Consumidor
    participant CANAL as Canal P2P Local
    participant TFL_P as TFLite Proveedor
    participant APP_P as App Proveedor
    participant API as Backend REST

    C->>APP_C: Captura imagen desde camara o galeria
    APP_C->>APP_C: Redimensiona a 224x224 px y normaliza pixeles
    APP_C->>TFL_C: Ejecuta capas iniciales de MobileNetV3
    Note over TFL_C: Fragmento 1 del modelo - primeras capas
    activate TFL_C
    TFL_C-->>APP_C: Tensor de activacion intermedio (feature map)
    deactivate TFL_C
    APP_C->>APP_C: Serializa tensor con Protocol Buffers
    Note over APP_C: Sobrecarga maxima de serializacion: 80 ms

    APP_C->>CANAL: Envia tensor serializado al proveedor
    Note over CANAL: Cifrado TLS v1.3 -- Protocolo de app. sujeto a cambio
    CANAL->>APP_P: Tensor recibido en nodo proveedor
    APP_P->>TFL_P: Ejecuta capas finales de MobileNetV3
    Note over TFL_P: Fragmento 2 del modelo - capas finales
    activate TFL_P
    TFL_P-->>APP_P: Vector de clasificacion final (logits + softmax)
    deactivate TFL_P
    APP_P->>APP_P: Empaqueta resultado con clase y porcentaje de confianza
    APP_P->>CANAL: Retorna resultado de clasificacion al consumidor
    CANAL-->>APP_C: Resultado de clasificacion recibido

    APP_C->>APP_C: Calcula latencia total del ciclo completo
    Note over APP_C,C: Latencia total maxima extremo a extremo: 1500 ms
    APP_C-->>C: Muestra clase detectada y porcentaje de confianza

    APP_C->>API: POST /transacciones (idConsumidor, idProveedor, monto)
    API-->>APP_C: 201 Transaccion registrada exitosamente
```

---

### DS-06 · Inferencia en Modo Fallback Local (CU-06 - Escenario alternativo)

```mermaid
sequenceDiagram
    actor C as Consumidor
    participant APP_C as App Consumidor
    participant CANAL as Canal P2P Local
    participant TFL_C as TFLite Consumidor
    participant API as Backend REST

    C->>APP_C: Captura imagen y solicita clasificacion
    APP_C->>APP_C: Preprocesa imagen a 224x224 px
    APP_C->>CANAL: Intenta establecer conexion con nodo proveedor

    alt Timeout mayor a 800 ms o proveedor desconectado
        CANAL-->>APP_C: Fallo de conexion o timeout superado
        APP_C->>APP_C: Activa modo FALLBACK local automaticamente
        APP_C->>TFL_C: Ejecuta MobileNetV3 completo en dispositivo local
        Note over TFL_C: Modelo completo sin division -- Maximo 3000 ms
        activate TFL_C
        TFL_C-->>APP_C: Resultado de clasificacion local completo
        deactivate TFL_C
        APP_C->>APP_C: Marca resultado con fueLocal = true
        APP_C-->>C: Muestra resultado con indicador Modo Local
        alt Backend disponible via WAN
            APP_C->>API: Notifica tarea completada en modo local
            API-->>APP_C: 200 OK - Evento registrado
        else Backend no disponible
            APP_C->>APP_C: Encola evento para sincronizacion diferida
            Note over APP_C: Se sincroniza cuando se restablezca el enlace WAN
        end
    else Proveedor disponible antes del timeout
        CANAL-->>APP_C: Conexion establecida correctamente
        APP_C-->>C: Continua con inferencia distribuida normal
    end
```

---

### DS-07 · Registro y Consulta de Recompensas (CU-08, CU-10)

```mermaid
sequenceDiagram
    participant APP_C as App Consumidor
    participant API as Backend REST
    participant DB as Base de Datos Central
    participant APP_P as App Proveedor

    Note over APP_C,DB: Registro automatico tras completar inferencia distribuida

    APP_C->>API: POST /transacciones (idSolicitud, idConsumidor, idProveedor, monto)
    Note over APP_C,API: JWT en header de autorizacion sobre HTTPS
    activate API
    API->>DB: BEGIN TRANSACTION (aislamiento ACID)
    API->>DB: INSERT INTO Historial_Contribuciones
    API->>DB: UPDATE saldo_proveedor += monto
    API->>DB: UPDATE saldo_consumidor -= monto

    alt Transaccion exitosa
        DB-->>API: COMMIT exitoso
        API-->>APP_C: 201 Created - idTransaccion y estado EXITOSA
        deactivate API
        APP_C->>APP_C: Actualiza historial local del consumidor
    else Fallo en alguna operacion de base de datos
        DB-->>API: ROLLBACK automatico
        API-->>APP_C: 500 Internal Server Error - estado FALLIDA
        APP_C->>APP_C: Encola transaccion para reintento posterior
    end

    Note over APP_P,DB: Consulta voluntaria de recompensas por el proveedor

    APP_P->>API: GET /recompensas con JWT del proveedor en header
    activate API
    API->>DB: SELECT saldo e historial WHERE idProveedor
    DB-->>API: Saldo acumulado e historial de contribuciones
    API-->>APP_P: 200 OK - saldo actual y lista de tareas completadas
    deactivate API
    APP_P->>APP_P: Actualiza vista de recompensas en pantalla
```

---

### DS-08 · Cierre de Sesion (CU-11)

```mermaid
sequenceDiagram
    actor U as Usuario
    participant APP as App Android
    participant BG as Background Service
    participant API as Backend REST

    U->>APP: Solicita cerrar sesion
    opt Usuario es Proveedor con nodo activo
        APP->>BG: Envia senal de apagado ordenado
        activate BG
        BG->>BG: Deja de anunciar disponibilidad en mDNS
        BG->>BG: Cierra sockets locales de comunicacion
        BG->>BG: Finaliza hilos de procesamiento activos
        BG-->>APP: Android Service detenido correctamente
        deactivate BG
    end
    APP->>API: POST /auth/logout con token JWT en header
    API-->>APP: 200 OK - Token revocado en servidor
    APP->>APP: Elimina token JWT de memoria volatil
    APP->>APP: Limpia datos de sesion y cache de la aplicacion
    APP-->>U: Redirige a pantalla de Login
```

---

## 2. Diagrama de Arquitectura de Componentes

```mermaid
graph TB
    subgraph MOBILE["CAPA MOVIL (Android API 29+)"]
        subgraph CONS["Dispositivo Consumidor"]
            C_UI["UI - Kotlin + XML\nCameraX API"]
            C_AUTH["Modulo de Autenticacion"]
            C_DISC["Modulo Descubrimiento mDNS"]
            C_PRE["Modulo Preprocesamiento\nImagen 224x224 px"]
            C_SPLIT["Modulo Split Computing\nCapas iniciales MobileNetV3"]
            C_SER["Modulo Serializacion\nProtocol Buffers"]
            C_FALL["Modulo Fallback Local\nMobileNetV3 completo"]
            C_REW["Modulo Recompensas\ny Transacciones"]
            C_TFLITE["TFLite Runtime\nFragmento 1"]
            C_DB[("Room / SQLite\nHistorial local")]
        end

        subgraph PROV["Dispositivo Proveedor"]
            P_UI["UI - Kotlin + XML"]
            P_AUTH["Modulo de Autenticacion"]
            P_PUB["Modulo Publicacion\nNodo mDNS"]
            P_RECV["Modulo Recepcion\ny Procesamiento"]
            P_REW["Modulo Recompensas\ny Transacciones"]
            P_TFLITE["TFLite Runtime\nFragmento 2"]
            P_BG["Android Background Service"]
            P_DB[("Room / SQLite\nHistorial local")]
        end
    end

    subgraph LAN["RED WIFI LOCAL (LAN - min 20 Mbps)"]
        MDNS["Protocolo mDNS\nDescubrimiento de servicios"]
        P2P["Canal P2P - TLS v1.3\nProtocolo de app. sujeto a cambio"]
    end

    subgraph BACK["BACKEND EXTERNO (WAN)"]
        GW["API Gateway\nJWT + HTTPS"]
        REST["Servicio REST\nAuth y Transacciones"]
        WS["WebSockets\nSincronizacion en tiempo real"]
        DB[("Base de Datos Central\nPostgreSQL o MySQL")]
    end

    C_UI --> C_PRE
    C_UI --> C_DISC
    C_UI --> C_AUTH
    C_PRE --> C_SPLIT
    C_SPLIT --> C_TFLITE
    C_SPLIT --> C_SER
    C_SER --> P2P
    C_FALL --> C_TFLITE
    C_DISC --> MDNS
    C_AUTH --> GW
    C_REW --> GW
    C_DB <--> C_REW

    P_PUB --> MDNS
    P_PUB --> P_BG
    P_BG --> P_RECV
    P_RECV --> P_TFLITE
    P2P --> P_RECV
    P_AUTH --> GW
    P_REW --> GW
    P_DB <--> P_REW
    P_UI --> P_AUTH
    P_UI --> P_PUB

    GW --> REST
    GW --> WS
    REST --> DB
    WS --> DB
```

---

## 3. Diagrama de Navegacion

```mermaid
flowchart TD
    SPLASH(["Inicio / Splash Screen"])
    LOGIN["Pantalla de Login\nCU-02"]
    REG["Pantalla de Registro\nCU-01"]

    subgraph CONSUMER_FLOW["Flujo del Consumidor"]
        DASH_C["Dashboard Consumidor"]
        NODOS["Nodos Disponibles\nCU-04"]
        CAP["Seleccion de Imagen\nCamara o Galeria - CU-05"]
        PROC["Procesando...\nInferencia Distribuida - CU-06"]
        RES["Resultado de Clasificacion\nClase + Confianza + Latencia - CU-07"]
        HIST_C["Historial de Inferencias\ny Transacciones"]
    end

    subgraph PROVIDER_FLOW["Flujo del Proveedor"]
        DASH_P["Dashboard Proveedor"]
        COLA["Activar Modo Colaborador\nCU-03"]
        MON["Monitor del Nodo\nEstado y metricas - CU-10"]
        HIST_P["Historial de Recompensas\nCU-08"]
        DESAC["Desactivar Nodo\nCU-09"]
    end

    SPLASH --> LOGIN
    LOGIN -->|"Sin cuenta"| REG
    REG -->|"Rol = CONSUMIDOR"| DASH_C
    REG -->|"Rol = PROVEEDOR"| DASH_P
    LOGIN -->|"Rol = CONSUMIDOR"| DASH_C
    LOGIN -->|"Rol = PROVEEDOR"| DASH_P

    DASH_C --> NODOS
    DASH_C --> CAP
    DASH_C --> HIST_C
    NODOS -->|"Nodo seleccionado y conectado"| DASH_C
    CAP --> PROC
    PROC -->|"Inferencia distribuida completada"| RES
    PROC -->|"Fallback local activado"| RES
    RES -->|"Nueva clasificacion"| CAP
    RES -->|"Volver al inicio"| DASH_C

    DASH_P --> COLA
    DASH_P --> MON
    DASH_P --> HIST_P
    COLA -->|"Nodo activado exitosamente"| MON
    MON --> DESAC
    DESAC -->|"Nodo desactivado"| DASH_P

    DASH_C -->|"Cerrar sesion - CU-11"| LOGIN
    DASH_P -->|"Cerrar sesion - CU-11"| LOGIN
```

---

## 4. Diagrama de Dominio

```mermaid
classDiagram
    direction TB

    class Usuario {
        +UUID id
        +String nombre
        +String correo
        +String contrasenaHash
        +Rol rol
        +Double saldo
    }

    class Dispositivo {
        +UUID id
        +String direccionIP
        +EstadoNodo estado
        +UUID idUsuario
        +Integer tareasCompletadas
        +activarModo()
        +desactivarModo()
    }

    class SolicitudDeProcesamiento {
        +UUID id
        +ByteArray imagenOrigen
        +Long timestamp
        +EstadoSolicitud estado
        +UUID idConsumidor
        +UUID idNodoAsignado
        +Long latenciaTotal
        +iniciarDistribuida()
        +activarFallback()
    }

    class FragmentoDeModelo {
        +UUID id
        +String capasIncluidas
        +String rutaArchivo
        +IntArray tensorEntrada
        +IntArray tensorSalida
        +ejecutar()
        +serializar()
    }

    class Transaccion {
        +UUID id
        +UUID idSolicitud
        +UUID idConsumidor
        +UUID idProveedor
        +Double monto
        +Long timestamp
        +EstadoTransaccion estado
        +registrar()
        +revertir()
    }

    class ResultadoDeClasificacion {
        +UUID id
        +UUID idSolicitud
        +String claseDetectada
        +Float porcentajeConfianza
        +Long latenciaTotal
        +Boolean fueLocal
        +mostrar()
    }

    class Rol {
        <<enumeration>>
        CONSUMIDOR
        PROVEEDOR
    }

    class EstadoNodo {
        <<enumeration>>
        ACTIVO
        INACTIVO
    }

    class EstadoSolicitud {
        <<enumeration>>
        PENDIENTE
        EN_PROCESO
        COMPLETADA
        FALLBACK
    }

    class EstadoTransaccion {
        <<enumeration>>
        EXITOSA
        FALLIDA
    }

    Usuario "1" --> "1..*" Dispositivo : posee
    Usuario "1" --> "0..*" SolicitudDeProcesamiento : origina como consumidor
    Dispositivo "1" --> "0..*" SolicitudDeProcesamiento : asignado como proveedor
    SolicitudDeProcesamiento "1" *-- "2" FragmentoDeModelo : compuesta por
    SolicitudDeProcesamiento "1" --> "0..1" Transaccion : genera
    SolicitudDeProcesamiento "1" --> "0..1" ResultadoDeClasificacion : produce
    Transaccion --> Usuario : consumidor referenciado
    Transaccion --> Usuario : proveedor referenciado
    Usuario --> Rol : tiene asignado
    Dispositivo --> EstadoNodo : tiene
    SolicitudDeProcesamiento --> EstadoSolicitud : tiene
    Transaccion --> EstadoTransaccion : tiene
```

---

## 5. Diagrama de Despliegue

```mermaid
graph TD
    subgraph PHONE_C["Nodo Fisico: Dispositivo Consumidor\nAndroid API 29 o superior - min 3GB RAM - min 100MB storage"]
        APPC["Aplicacion Movil Consumidor\nKotlin"]
        TFLC["TFLite Runtime\nFragmento 1 MobileNetV3"]
        DBROOMC[("SQLite con Room\nHistorial local")]
        CAMX["CameraX API\nCaptura de imagen min 8MP"]
        MDNSC["Cliente mDNS\nDescubrimiento de nodos"]
        P2PC["Cliente P2P Local\nProtocolo sujeto a cambio"]
    end

    subgraph PHONE_P["Nodo Fisico: Dispositivo Proveedor\nAndroid API 29 o superior - min 3GB RAM - min 100MB storage"]
        APPP["Aplicacion Movil Proveedor\nKotlin"]
        TFLP["TFLite Runtime\nFragmento 2 MobileNetV3"]
        DBROOMP[("SQLite con Room\nHistorial local")]
        MDNSS["Servidor mDNS\nPublicacion de disponibilidad"]
        P2PS["Servidor P2P Local\nProtocolo sujeto a cambio"]
        BGS["Android Background Service\nEjecucion en segundo plano"]
    end

    subgraph LAN_WIFI["Red de Comunicacion Local WiFi\n802.11 - min 20 Mbps - latencia max 15 ms - max 15 nodos"]
        ROUTER["Access Point WiFi"]
        MDNS_NET["Servicio mDNS\nBroadcast en subred"]
        P2P_NET["Canal P2P - TLS v1.3\nProtocolo de aplicacion sujeto a cambio"]
    end

    subgraph WAN["Enlace de Red Externo WAN / Internet"]
        WAN_LINK["Conexion HTTPS\nJWT en headers de autorizacion"]
    end

    subgraph BACKEND["Servidor Backend - Cloud o On-premise"]
        APIGW_D["API Gateway\nJWT + HTTPS"]
        REST_D["Servicio REST\nAutenticacion y Transacciones"]
        WSD["Servicio WebSockets\nSincronizacion en tiempo real"]
        DBC[("Base de Datos Central\nPostgreSQL o MySQL\nRetencion min 2 meses")]
    end

    APPC --> TFLC
    APPC --> DBROOMC
    APPC --> CAMX
    APPC --> MDNSC
    APPC --> P2PC

    APPP --> TFLP
    APPP --> DBROOMP
    APPP --> MDNSS
    APPP --> BGS
    BGS --> P2PS

    MDNSC <-->|Descubrimiento de servicios| ROUTER
    MDNSS <-->|Publicacion de disponibilidad| ROUTER
    ROUTER <--> MDNS_NET
    P2PC <-->|Tensor intermedio cifrado TLS v1.3| P2P_NET
    P2PS <-->|Resultado de clasificacion cifrado| P2P_NET

    APPC <-->|REST HTTPS con JWT| WAN_LINK
    APPP <-->|REST HTTPS con JWT| WAN_LINK
    WAN_LINK --> APIGW_D
    APIGW_D --> REST_D
    APIGW_D --> WSD
    REST_D --> DBC
    WSD --> DBC
```

---

> **Leyenda de relaciones en diagrama de dominio:**
> - `*--` Composicion: el ciclo de vida del objeto hijo depende del padre
> - `-->` Asociacion: referencia entre entidades independientes
>
> **Leyenda de tecnologias usadas:**
> - **TFLite:** TensorFlow Lite para ejecucion del modelo MobileNetV3
> - **mDNS:** Multicast DNS (RFC 6762) para descubrimiento de servicios en LAN
> - **Protocol Buffers (proto3):** Serializacion de tensores intermedios
> - **JWT + HTTPS:** Autenticacion segura contra el backend externo
> - **TLS v1.3:** Cifrado de extremo a extremo en canal P2P local
> - **Room/SQLite:** Persistencia local en cada dispositivo Android
> - **CameraX:** API de Android Jetpack para captura de imagen
