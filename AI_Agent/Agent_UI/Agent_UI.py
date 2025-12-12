import logging
import os
from typing import Annotated

import vtk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode


#
# Agent_UI
#


class Agent_UI(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("Agent_UI")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "AGENT")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#Agent_UI">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")

        # Additional initialization step after application startup is complete
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
    inputfolder: str
    outputfolder: str
    modeagent: str

#
# Agent_UIWidget
#

import qt  # à mettre en haut du fichier si pas déjà

class TextEditEnterFilter(qt.QObject):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback

    def eventFilter(self, obj, event):
        import qt

        if event.type() == qt.QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()

            # Enter ou Return
            if key in (qt.Qt.Key_Return, qt.Qt.Key_Enter):
                # Shift+Enter -> nouvelle ligne, on laisse passer
                if modifiers & qt.Qt.ShiftModifier:
                    return False

                # Sinon, on lance la fonction
                self.callback()
                return True  # on consomme l'événement (pas de saut de ligne)

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

    def setup(self) -> None:
        import qt
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/Agent_UI.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        self.enterFilter = TextEditEnterFilter(self.ui.textEdit_2, self.onReturnPressed)
        self.ui.textEdit_2.installEventFilter(self.enterFilter)


        te = self.ui.textEdit_2

        # Hauteur d'une ligne selon la police
        fm = te.fontMetrics()
        lineHeight = fm.lineSpacing()

        minLines = 1
        maxLines = 6

        # Calcul des hauteurs min/max en pixels
        minHeight = int(lineHeight * minLines + te.frameWidth * 2 + 8)
        maxHeight = int(lineHeight * maxLines + te.frameWidth * 2 + 8)

        # Appliquer min / max
        te.setMinimumHeight(minHeight)
        te.setMaximumHeight(maxHeight)

        # Scrollbar seulement si besoin
        te.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)

        # Taille horizontale Expanding, verticale contrôlée par nous
        te.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Fixed)

        # Hauteur de départ = minimum (1 ligne)
        te.setFixedHeight(minHeight)

        # Fonction pour ajuster la hauteur en fonction du contenu
        def _autoResizeTextEdit():
            docHeight = te.document.size.height()
            h = int(docHeight) + 10  # petit padding
            if h < minHeight:
                h = minHeight
            if h > maxHeight:
                h = maxHeight
            te.setFixedHeight(h)

        # Quand le texte change, on ajuste la hauteur entre min et max
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
        
        # Connect UI signals to checkCanApply
        self.ui.textEdit_2.connect("textChanged()", self._checkCanApply)
        self.ui.PathLineEdit.connect("currentPathChanged(QString)", self._checkCanApply)
        self.ui.PathLineEdit_2.connect("currentPathChanged(QString)", self._checkCanApply)
        self.ui.comboBox.currentIndexChanged.connect(self._checkCanApply)


        self.ui.label_4.hide()

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()


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
        if not self._parameterNode.inputfolder:
            self._parameterNode.inputfolder = ""
        if not self._parameterNode.outputfolder:
            self._parameterNode.outputfolder = ""
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
            self.ui.PathLineEdit.blockSignals(True)
            self.ui.PathLineEdit_2.blockSignals(True)
            self.ui.comboBox.blockSignals(True)

            self.ui.textEdit_2.setPlainText(self._parameterNode.prompt or "")
            self.ui.PathLineEdit.setCurrentPath(self._parameterNode.inputfolder or "")
            self.ui.PathLineEdit_2.setCurrentPath(self._parameterNode.outputfolder or "")
            self.ui.comboBox.setCurrentText(self._parameterNode.modeagent or "Agent (Automated)")

            self.ui.textEdit_2.blockSignals(False)
            self.ui.PathLineEdit.blockSignals(False)
            self.ui.PathLineEdit_2.blockSignals(False)
            self.ui.comboBox.blockSignals(False)

            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        if not self._parameterNode:
            self.ui.applyButton.enabled = False
            self.ui.SaveButton.enabled = False
            self.ui.ClearButton.enabled = False
            return
        
        # Update parameter node values from UI
        self._parameterNode.prompt = self.ui.textEdit_2.toPlainText()
        self._parameterNode.inputfolder = self.ui.PathLineEdit.currentPath
        self._parameterNode.outputfolder = self.ui.PathLineEdit_2.currentPath
        self._parameterNode.modeagent = self.ui.comboBox.currentText
        
        # Check if all required fields are filled
        has_prompt = self._parameterNode.prompt.strip() != ""
        has_input = self._parameterNode.inputfolder.strip() != ""
        has_output = self._parameterNode.outputfolder.strip() != ""
        
        if has_prompt and has_input and has_output:
            self.ui.applyButton.toolTip = _("Click to give your prompt to the agent")
            self.ui.applyButton.enabled = True
        else:
            missing = []
            if not has_prompt:
                missing.append("prompt")
            if not has_input:
                missing.append("input folder")
            if not has_output:
                missing.append("output folder")
            self.ui.applyButton.toolTip = _(f"Fill: {', '.join(missing)}")
            self.ui.applyButton.enabled = False

        if self.ui.textEdit.toPlainText()!="":
            self.ui.SaveButton.toolTip = _("Click to save your chat with the agent")
            self.ui.SaveButton.enabled = True
            self.ui.ClearButton.toolTip = _("Click to clear your chat with the agent")
            self.ui.ClearButton.enabled = True
        else:
            self.ui.ClearButton.toolTip = _(f"Start a chat with the LLM to be able to save")
            self.ui.ClearButton.enabled = False
            self.ui.SaveButton.toolTip = _(f"Start a chat with the LLM to be able to save")
            self.ui.SaveButton.enabled = False

    def eventFilter(self, obj, event):
        import qt

        # On intercepte les touches dans textEdit_2
        if obj == self.ui.textEdit_2 and event.type() == qt.QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()

            # Enter ou Return
            if key in (qt.Qt.Key_Return, qt.Qt.Key_Enter):
                # Si Shift+Enter -> on laisse faire (nouvelle ligne)
                if modifiers & qt.Qt.ShiftModifier:
                    return False  # ne consomme pas l'événement

                # Sinon, on lance la fonction (par ex. onApplyButton)
                if self.ui.applyButton.isEnabled():
                    self.onReturnPressed()
                else:
                    # pour debug si tu veux
                    print("Apply button disabled, Enter ignoré.")
                return True  # on consomme l'événement (pas de saut de ligne)

        # Pour tout le reste, comportement normal
        return super().eventFilter(obj, event)

    def to_html(self, text):
        """Échappe le texte pour le HTML tout en préservant la mise en forme."""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#39;")
        # Convertir les retours à la ligne en <br>
        text = text.replace("\n", "<br>")
        # Convertir les espaces multiples en espaces insécables
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

    def onApplyButton(self) -> None:
        import time
        self.CliStartTime = time.time()
        self.ui.label_4.setVisible(True)
        slicer.app.processEvents()

        message = "👨:" + self._parameterNode.prompt
        self.add_user_message(message)

        cliParams = {
            "inputfolder": self._parameterNode.inputfolder,
            "outputfolder": self._parameterNode.outputfolder,
            "prompt": self._parameterNode.prompt,
            "modeagent": self._parameterNode.modeagent
        }

        CLI = slicer.modules.agent_cli

        # lancement ASYNCHRONE
        self.cliNode = slicer.cli.run(CLI, None, cliParams)

        # observer les changements de status
        self.addObserver(self.cliNode, vtk.vtkCommand.ModifiedEvent, self.onCliUpdated)

        # éventuellement désactiver le bouton Apply pendant le run
        self.ui.applyButton.enabled = False
        self.ui.textEdit_2.clear()

    def onCliUpdated(self, caller, event):
        import time
        import json
        import subprocess
        cliNode = caller

        status = cliNode.GetStatus()

        # statut terminé (Completed / Failed / Cancelled)
        if status & slicer.vtkMRMLCommandLineModuleNode.Completed or \
           status & slicer.vtkMRMLCommandLineModuleNode.Cancelled:

            # on n’a plus besoin de l’observer
            self.removeObserver(cliNode, vtk.vtkCommand.ModifiedEvent, self.onCliUpdated)

            # cacher le label
            self.ui.applyButton.enabled = True

            # récupérer le texte de sortie
            output_text = cliNode.GetOutputText()
            output_text = output_text.replace("*","")
            output_text = output_text.replace("#","")

            if self._parameterNode.modeagent == "Agent (Automated)":
                message = json.loads(output_text)
                selected_tool = message.get("tool","")
                missing_required = message.get("missing_required",[])
                params = message.get("parameters",{})
                cli_args = message.get("command",[])

                if selected_tool:
                    if len(missing_required) > 0:
                        output_text = f"""After reflexion I would like to run {selected_tool} but I need more parameters: {missing_required} """
                        self.add_agent_message(output_text)
                    else:
                        output_text = f"""After reflexion I would like to run {selected_tool} with this parameters: {params} """

                        reply = qt.QMessageBox.question(
                            None,
                            f"Run {selected_tool}",
                            f"The agent want to run {selected_tool} with this parameter: {params}?",
                            qt.QMessageBox.Yes | qt.QMessageBox.No
                        )

                        if reply == qt.QMessageBox.Yes:
                            output_text+=f"\nRunning:{selected_tool}\n"
                            self.add_agent_message(output_text)

                            newText = f"LLM is running {selected_tool}"
                            self.ui.label_4.setText(newText)

                            result = subprocess.run(cli_args, capture_output=True, text=True)

                            stdout = result.stdout.strip()
                            stderr = result.stderr.strip()

                            print(stdout)
                            print(stderr)
                        
                else:
                    output_text = f"""After reflexion I wasn't able to choose a module to run. Try to explain me your need in a other way."""
                    self.add_agent_message(output_text)

            self.ui.label_4.setVisible(False)
            self._checkCanApply()
        
        act_time = time.time()
        total_time = round(act_time-self.CliStartTime,2)
        newText = f"LLM is thinking ({total_time}s)"
        self.ui.label_4.setText(newText)

    def OnSaveButton(self):
        import time

        text=self.ui.textEdit.toPlainText()
        filename = f"{self._parameterNode.outputfolder}/Chat_LLM_{time.strftime('%Y-%m-%d_%H-%M-%S')}.txt"

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
        
        output_list = content.split("🤖: ")

        if len(output_list)<2:
            qt.QMessageBox.warning(None,"Text file incompatible","Please choose a text (.txt) file from a previous discussion with the agent")
        else:
            for message in output_list:
                if message.startswith("👨:"):
                    self.add_user_message(message)
                else:
                    self.add_agent_message(message)

            self._checkCanApply()

#
# Agent_UILogic
#

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
                inputfolder: str,
                outputfolder: str,
                prompt: str) -> str:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputfolder: folder contenant les inputs
        :param outputfolder: folder pour les outputs
        :param prompt: prompt pour l'agent
        :return: output text du CLI
        """

        import time
        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "inputfolder": inputfolder,
            "outputfolder": outputfolder,
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
