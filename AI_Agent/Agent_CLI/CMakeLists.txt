#-----------------------------------------------------------------------------
set(MODULE_NAME Agent_CLI)
set(FOLDER_LIBRARY Agent_CLI_utils)

set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  ${FOLDER_LIBRARY}/utils.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/UI/${MODULE_NAME}.ui
  )

SlicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
)
