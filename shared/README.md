# Shared  
  
Modulo de utilidades y recursos compartidos entre los subproyectos social y economico.  
  
## Proposito  
  
Este subproyecto contiene:  
- Funciones utilitarias comunes  
- Configuraciones compartidas  
- Utilidades de procesamiento de datos  
- Constantes y configuraciones globales  
- Helpers de visualizacion  
  
## Estructura  
  
shared/  
ÃÄÄ utils/              # Funciones utilitarias  
ÃÄÄ config/             # Configuraciones compartidas  
ÃÄÄ constants/          # Constantes globales  
ÀÄÄ helpers/            # Helpers de uso general  
  
## Uso  
  
from shared.utils import load_data, preprocess  
from shared.config import settings  
from shared.constants import VARIABLES  
  
## Dependencias  
  
Este modulo no depende de social ni economico, pero ambos pueden depender de el. 
