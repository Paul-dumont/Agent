import logging
import os
from typing import Annotated
import qt
import vtk
import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange)

from slicer import vtkMRMLScalarVolumeNode

class DropZone(qt.QFrame):
    """Zone drag&drop multi-fichiers/dossiers. Émet une liste de paths locaux."""
    dropped = qt.Signal(list)

    def __init__(self, parent=None, title="Drop files or folders here",objectName = "dropZone"):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName(objectName)
        self.setFrameShape(qt.QFrame.StyledPanel)
        self.setFrameShadow(qt.QFrame.Plain)
        self.setMinimumHeight(100)

        self._label = qt.QLabel(title)
        self._label.alignment = qt.Qt.AlignCenter

        lay = qt.QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(self._label)

        # style “drop zone”
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #b8c4d6;
                border-radius: 8px;
                background: #ffffff;
            }
            QLabel {
                color: #34495e;
                font-weight: 800;
            }
        """)

    def dragEnterEvent(self, event):
        md = event.mimeData()
        if md.hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        paths = []
        for u in urls:
            if u.isLocalFile():
                p = u.toLocalFile()
                if p:
                    paths.append(p)

        if paths:
            self.dropped.emit(paths)

        event.acceptProposedAction()
    
    def setSummary(self, paths):
        if not paths:
            self._label.setText("Drop files or folders here")
            return

        preview = "\n".join(paths[:3])
        more = "" if len(paths) <= 3 else f"\n... (+{len(paths)-3} more)"
        self._label.setText(f"Dropped {len(paths)} item(s):\n{preview}{more}")

#
# Agent_UI
#


class Agent_UI(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("Agent_UI")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "AGENT")]
        self.parent.dependencies = []
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#Agent_UI">module documentation</a>.
""")
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")

        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # Agent_UI1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="Agent_UI",
        sampleName="Agent_UI1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "Agent_UI1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="Agent_UI1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="Agent_UI1",
    )

    # Agent_UI2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="Agent_UI",
        sampleName="Agent_UI2",
        thumbnailFileName=os.path.join(iconsPath, "Agent_UI2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="Agent_UI2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="Agent_UI2",
    )


#
# Agent_UIParameterNode
#


@parameterNodeWrapper
class Agent_UIParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    prompt: str
    folders: list
    modeagent: str

#
# Agent_UIWidget
#

# import qt

class TextEditEnterFilter(qt.QObject):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback

    def eventFilter(self, obj, event):
        import qt

        if event.type() == qt.QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()

            # Enter
            if key in (qt.Qt.Key_Return, qt.Qt.Key_Enter):
                # Shift+Enter -> New line
                if modifiers & qt.Qt.ShiftModifier:
                    return False
                self.callback()
                return True

        return False



class Agent_UIWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None
        self.CliStartTime=0
        self._requiredWidgets = {}

    def setup(self) -> None:
        import qt
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/Agent_UI.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        self.dropZone = DropZone(objectName="dropZoneInput")

        self.dropZoneButton = qt.QPushButton("x")

        self.dropZoneButton.setStyleSheet("""
        QPushButton {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                            stop:0 #e74c3c, /* Rouge vif */
                                            stop:1 #c0392b); /* Rouge légèrement plus foncé */
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 10pt;
            padding: 8px; 
            margin-top: 4px; /* Déplacer cette déclaration ici */
        }

        QPushButton:hover:!pressed {
            /* Rouge plus clair au survol */
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                            stop:0 #e9685a, /* Rouge vif légèrement éclairci */
                                            stop:1 #d64d3c);
        }

        QPushButton:pressed {
            /* Rouge foncé au clic (effet d'enfoncement) */
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                            stop:0 #a93226, /* Rouge très foncé */
                                            stop:1 #8e241b);
        }

        QPushButton:disabled {
            /* État désactivé (gris) */
            background-color: #bdc3c7;
            color: #95a5a6;
        }
        """)

        self.dropZoneLayout = qt.QHBoxLayout()

        self.dropZoneLayout.setContentsMargins(0, 0, 0, 0)
        self.dropZoneLayout.setSpacing(5)

        self.dropZoneLayout.addWidget(self.dropZone,98)
        self.dropZoneLayout.addWidget(self.dropZoneButton,2)

        self.dropZoneContainer = qt.QWidget()
        self.dropZoneContainer.setLayout(self.dropZoneLayout)

        self.ui.formLayout_2.addRow("Drop zone", self.dropZoneContainer)

        self.dropZone.dropped.connect(self.onDroppedPaths)

        # Retrieve the list
        self.droppedInputPaths = []

        self.enterFilter = TextEditEnterFilter(self.ui.textEdit_2, self.onReturnPressed)
        self.ui.textEdit_2.installEventFilter(self.enterFilter)

        te = self.ui.textEdit_2

        fm = te.fontMetrics()
        lineHeight = fm.lineSpacing()

        minLines = 1
        maxLines = 6

        minHeight = int(lineHeight * minLines + te.frameWidth * 2 + 8)
        maxHeight = int(lineHeight * maxLines + te.frameWidth * 2 + 8)

        te.setMinimumHeight(minHeight)
        te.setMaximumHeight(maxHeight)

        te.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)

        te.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Fixed)

        te.setFixedHeight(minHeight)

        def _autoResizeTextEdit():
            docHeight = te.document.size.height()
            h = int(docHeight) + 10  # little padding
            if h < minHeight:
                h = minHeight
            if h > maxHeight:
                h = maxHeight
            te.setFixedHeight(h)

        te.textChanged.connect(_autoResizeTextEdit)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = Agent_UILogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)
        self.ui.SaveButton.connect("clicked(bool)", self.OnSaveButton)
        self.ui.ClearButton.connect("clicked(bool)", self.OnClearButton)
        self.ui.RetrieveButton.connect("clicked(bool)",self.OnRetrieveButton)
        self.ui.CheckButton.connect("clicked(bool)",self.CheckDependencies)
        
        # Connect UI signals to checkCanApply
        self.ui.textEdit_2.connect("textChanged()", self._checkCanApply)
        self.ui.comboBox.currentIndexChanged.connect(self._checkCanApply)
        self.dropZoneButton.connect("clicked(bool)",self.clearDropzone)


        self.ui.label_4.hide()

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def onDroppedPaths(self, paths):
        norm = []
        seen = set()
        for p in paths:
            p = os.path.normpath(p)
            if p not in seen:
                seen.add(p)
                norm.append(p)
        for path in norm:
            self.droppedInputPaths.append(path)

        # Show summary in the drop area
        self.dropZone.setSummary(self.droppedInputPaths)
        self._checkCanApply()

    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        # if self._parameterNode:
        #     self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
        #     self._parameterNodeGuiTag = None
        #     self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes only if they are not already set
        if not self._parameterNode.prompt:
            self._parameterNode.prompt = ""
        if not self._parameterNode.folders:
            self._parameterNode.folders = []
        if not self._parameterNode.modeagent:
            self._parameterNode.modeagent = "Agent (Automated)"


    def setParameterNode(self, inputParameterNode: Agent_UIParameterNode | None) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """
        self._parameterNode = inputParameterNode

        if self._parameterNode:
            self.ui.textEdit_2.blockSignals(True)
            self.ui.comboBox.blockSignals(True)

            self.ui.textEdit_2.setPlainText(self._parameterNode.prompt or "")
            self.ui.comboBox.setCurrentText(self._parameterNode.modeagent or "Agent (Automated)")

            self.ui.textEdit_2.blockSignals(False)
            self.ui.comboBox.blockSignals(False)

            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        if not self._parameterNode:
            self.ui.applyButton.enabled = False
            self.ui.SaveButton.enabled = False
            self.ui.ClearButton.enabled = False
            self.ui.CheckButton.enabled = False
            return
        
        # Update parameter node values from UI
        self._parameterNode.prompt = self.ui.textEdit_2.toPlainText()
        self._parameterNode.modeagent = self.ui.comboBox.currentText
        self._parameterNode.folders = self.droppedInputPaths
        
        # Check if all required fields are filled
        has_prompt = self._parameterNode.prompt.strip() != ""
        has_folders = self._parameterNode.folders != []

        if self._parameterNode.modeagent == "Agent (Automated)":
            if has_prompt and has_folders and not self.ui.label_4.isVisible():
                self.ui.applyButton.toolTip = _("Click to give your prompt to the agent")
                self.ui.applyButton.enabled = True
            else:
                missing = []
                if not has_prompt:
                    missing.append("prompt")
                if not has_folders:
                    missing.append("folders")
                self.ui.applyButton.toolTip = _(f"Fill: {', '.join(missing)}")
                self.ui.applyButton.enabled = False
        else:
            if has_prompt and not self.ui.label_4.isVisible():
                self.ui.applyButton.toolTip = _("Click to give your prompt to the agent")
                self.ui.applyButton.enabled = True
            else:
                missing = []
                if not has_prompt:
                    missing.append("prompt")
                self.ui.applyButton.toolTip = _(f"Fill: {', '.join(missing)}")
                self.ui.applyButton.enabled = False


        if self.ui.textEdit.toPlainText()!="":
            self.ui.SaveButton.toolTip = _("Click to save your chat with the agent")
            self.ui.SaveButton.enabled = True
            self.ui.ClearButton.toolTip = _("Click to clear your chat with the agent")
            self.ui.ClearButton.enabled = True
        else:
            self.ui.ClearButton.toolTip = _(f"Start a chat with the LLM to be able to clear it")
            self.ui.ClearButton.enabled = False
            self.ui.SaveButton.toolTip = _(f"Start a chat with the LLM to be able to save it")
            self.ui.SaveButton.enabled = False

    def to_html(self, text):
        """Échappe le texte pour le HTML tout en préservant la mise en forme."""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#39;")

        text = text.replace("\n", "<br>")

        text = text.replace("  ", "&nbsp;&nbsp;")
        return text

    def add_user_message(self, msg):
        msg_escaped = self.to_html(msg)
        self.ui.textEdit.insertHtml(
            f'<table width="100%"><tr><td width="20%"></td><td width="80%" align="right">'
            f'<div style="color: #3498db; padding: 6px 15px; border-radius: 999px; margin: 5px 20px 5px 0; display: inline-block; white-space: pre-wrap; font-family: Segoe UI, Arial, sans-serif; font-size: 11pt;">'
            f'{msg_escaped}'
            f'</div>'
            f'</td></tr></table>'
        )
        cursor = self.ui.textEdit.textCursor()
        cursor.movePosition(qt.QTextCursor.End)
        self.ui.textEdit.setTextCursor(cursor)
        self.ui.textEdit.ensureCursorVisible()

    def add_agent_message(self, msg):
        msg_escaped = self.to_html(msg)
        self.ui.textEdit.insertHtml(
            f'<table width="100%"><tr><td width="80%" align="left">'
            f'<div style="color: black; padding: 6px 15px; border-radius: 999px; margin: 5px 0 5px 20px; display: inline-block; white-space: pre-wrap; font-family: Segoe UI, Arial, sans-serif; font-size: 11pt;">'
            f'<b>🤖:</b> {msg_escaped}'
            f'</div>'
            f'</td><td width="20%"></td></tr></table>'
        )

        cursor = self.ui.textEdit.textCursor()
        cursor.movePosition(qt.QTextCursor.End)
        self.ui.textEdit.setTextCursor(cursor)
        self.ui.textEdit.ensureCursorVisible()

    def normalize_folders(self,folders):
        if folders is None:
            return []
        if isinstance(folders, (list, tuple)):
            return list(folders)
        try:
            # ObservedList, Qt list, etc.
            return list(folders)
        except TypeError:
            return [str(folders)]

    def onApplyButton(self) -> None:
        import time
        self.CliStartTime = time.time()
        self.ui.label_4.setVisible(True)
        slicer.app.processEvents()

        message = "👨:" + self._parameterNode.prompt
        self.add_user_message(message)

        self.droppedInputPaths = self.normalize_folders(self.droppedInputPaths)

        if not self.droppedInputPaths:
            self.droppedInputPaths.append(['nothing'])

        cliParams = {
            "folders": self.droppedInputPaths,
            "prompt": self._parameterNode.prompt,
            "modeagent": self._parameterNode.modeagent,
            "temp_folder":slicer.util.tempDirectory()
        }
        CLI = slicer.modules.agent_cli
            
        self.cliNode = slicer.cli.run(CLI, None, cliParams)

        if 'nothing' in self.droppedInputPaths:
            self.droppedInputPaths.remove('nothing')

        self.addObserver(self.cliNode, vtk.vtkCommand.ModifiedEvent, self.onCliUpdated)

        self.ui.applyButton.enabled = False
        self.ui.textEdit_2.clear()

    def showRequiredParameters(self, required_parameters):
        """
        required_parameters: list[dict] (ce que ton CLI renvoie)
        """
        layout = self.paramsFormLayout

        # Clear form
        while layout.rowCount() > 0:
            layout.removeRow(0)

        self._requiredWidgets = {}

        for p in required_parameters:
            name = p["name"]
            ptype = p.get("type", "str")
            desc = p.get("description", "")
            val  = p.get("value", None)
            miss = bool(p.get("is_missing", False))

            label = qt.QLabel(f"{name} *")
            label.setToolTip(desc)

            w = self._makeWidgetForRequired(ptype)
            self._setWidgetValue(w, ptype, val)

            if miss:
                label.setStyleSheet("color: #b00020; font-weight: 600;")

            layout.addRow(label, w)
            self._requiredWidgets[name] = (p, w)

    def _makeWidgetForRequired(self, ptype: str):
        import ctk
        if ptype == "path":
            w = ctk.ctkPathLineEdit()
            w.filters = ctk.ctkPathLineEdit.Files | ctk.ctkPathLineEdit.Dirs
            return w

        if ptype == "bool":
            return qt.QCheckBox()

        if ptype == "int":
            sb = qt.QSpinBox()
            sb.minimum = -10**9
            sb.maximum =  10**9
            return sb

        if ptype == "float":
            dsb = qt.QDoubleSpinBox()
            dsb.minimum = -1e12
            dsb.maximum =  1e12
            dsb.decimals = 6
            return dsb

        # list / list[float] / list[int] / str
        return qt.QLineEdit()
    
    def _setWidgetValue(self, w, ptype: str, val):
        if val is None:
            val = ""

        if ptype == "path":
            w.setCurrentPath(str(val) if val else "")
            return

        if ptype == "bool":
            w.checked = bool(val)
            return

        if ptype == "int":
            try: w.value = int(val)
            except: w.value = 0
            return

        if ptype == "float":
            try: w.value = float(val)
            except: w.value = 0.0
            return

        # list/str → text
        w.text = str(val)

    def _getWidgetValue(self, w, ptype: str):
        if ptype == "path":
            return w.currentPath

        if ptype == "bool":
            return bool(w.checked)

        if ptype == "int":
            return int(w.value)

        if ptype == "float":
            return float(w.value)

        return w.text
    
    def collectRequiredCorrections(self):
        corrections = {}
        for name, (pdef, w) in self._requiredWidgets.items():
            ptype = pdef.get("type", "str")
            corrections[name] = self._getWidgetValue(w, ptype)
        return corrections


    def onCliUpdated(self, caller, event):
        import time
        import json
        import subprocess
        cliNode = caller

        status = cliNode.GetStatus()

        if status & slicer.vtkMRMLCommandLineModuleNode.Completed or \
           status & slicer.vtkMRMLCommandLineModuleNode.Cancelled:

            self.removeObserver(cliNode, vtk.vtkCommand.ModifiedEvent, self.onCliUpdated)

            self.ui.applyButton.enabled = True

            output_text = cliNode.GetOutputText()
            print(output_text)

            if self._parameterNode.modeagent == "Agent (Automated)":
                message = json.loads(output_text)
                selected_tool = message.get("tool",None)
                missing_required = message.get("missing_required",[]) 
                params = message.get("parameters",{})
                cli_args = message.get("command",[])

                if selected_tool:
                    if missing_required == []:
                        output_text = f"""After reflexion I would like to run {selected_tool}. Click on the Yes button to launch the module if the parameters are good for you"""
                        self.add_agent_message(output_text)

                        parameters = "\n-".join(f"{key}={value}" for key, value in params.items())

                        reply = qt.QMessageBox.question(
                            None,
                            f"Run {selected_tool}",
                            f"The agent want to run {selected_tool} with this parameter:\n\n-{parameters}\n\n If it seems good for you, click on the Yes button, else on the No button",
                            qt.QMessageBox.Yes | qt.QMessageBox.No
                        )

                        if reply == qt.QMessageBox.Yes:
                            output_text=f"\nRunning:{selected_tool}\n"
                            self.add_agent_message(output_text)

                            newText = f"LLM is running {selected_tool}"
                            self.ui.label_4.setText(newText)

                            result = subprocess.run(cli_args, capture_output=True, text=True)

                            stdout = result.stdout.strip()
                            stderr = result.stderr.strip()
                            print(stdout)
                            print(stderr)

                    else:
                        missing = "\n-".join(missing_required)
                        output_text = f"""After reflexion I would like to run {selected_tool} but for this I need these parameters:\n\n-{missing}"""
                        self.add_agent_message(output_text)
                        
                else:
                    output_text = f"""After reflexion I wasn't able to choose a module to run. Try to explain me your need in a other way."""
                    self.add_agent_message(output_text)
            else:
                self.add_agent_message(output_text)

            self.ui.label_4.setVisible(False)
            self._checkCanApply()
        
        act_time = time.time()
        total_time = round(act_time-self.CliStartTime,2)
        newText = f"LLM is thinking ({total_time}s)"
        self.ui.label_4.setText(newText)

    def OnSaveButton(self):
        import time
        from pathlib import Path

        text=self.ui.textEdit.toPlainText()
        filename = f"{Path.home()}/Chat_LLM_{time.strftime('%Y-%m-%d_%H-%M-%S')}.txt"

        with open(filename, "w") as file:
            file.write(text)
        
        print(f"The chat has been saved to {filename}")
        self._checkCanApply()

    def OnClearButton(self):
        self.ui.textEdit.clear()
        self._checkCanApply()

    def onReturnPressed(self):
        if self.ui.applyButton.isEnabled():
            self.onApplyButton()
            
    def OnRetrieveButton(self):
        import qt
        fichier = qt.QFileDialog.getOpenFileName(
            None,
            "Choisir un fichier texte",
            "",
            "Fichiers texte (*.txt)"
        )

        with open(fichier, "r") as file:
            content = file.read()
        
        content = content.replace("🤖:","👨:")
        output_list = content.split("👨:")
        output_list.pop(0)
        print(output_list)

        if len(output_list)<2:
            qt.QMessageBox.warning(None,"Text file incompatible","Please choose a text (.txt) file from a previous discussion with the agent")
        else:
            for i in range (len(output_list)):
                if i%2 == 0:
                    self.add_user_message("👨:"+output_list[i])
                else:
                    self.add_agent_message(output_list[i])

            self._checkCanApply()

    def CheckDependencies(self):
        import subprocess

        slicer.util.pip_install("ollama")
        list_model = ["gemma","gemma2"]

        for model in list_model:
            try:
                subprocess.run(
                    ['ollama', 'pull',model],
                    capture_output=True,
                    text=True
                )
                print(f"Model {model} has successfully been installed")
                installed = True
            except Exception as e:
                print(f"Error getting models: {e}")
                installed = False
        
        if installed:
            qt.QMessageBox.information(None,"Dependencies checked and installed","All the dependencies have been checked and installed, now you can start to talk with your personal agent.")

        else:
            qt.QMessageBox.warning(None,"Dependencies installation issues","There has been an issue during the installation of the models, try again.")


    def clearDropzone(self):
        self.droppedInputPaths = []
        self.dropZone.setSummary(self.droppedInputPaths)
        self._checkCanApply()

class Agent_UILogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return Agent_UIParameterNode(super().getParameterNode())

    def process(self,
                folders: str,
                prompt: str) -> str:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param folders: folders contenant les inputs
        :param prompt: prompt pour l'agent
        :return: output text du CLI
        """

        import time
        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "folders": folders,
            "prompt": prompt
        }
        CLI = slicer.modules.agent_cli
        self.cliNode = slicer.cli.run(CLI,None, cliParams,wait=False)
        output_text = self.cliNode.GetOutputText()
        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")
        return output_text


#
# Agent_UITest
#


class Agent_UITest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_Agent_UI1()

    def test_Agent_UI1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("Agent_UI1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = Agent_UILogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
