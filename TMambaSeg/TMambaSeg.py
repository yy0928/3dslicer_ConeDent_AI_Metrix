import logging
import os
import qt
import pdb
import subprocess
from typing import Annotated, Optional
import glob

import vtk
import slicer
from slicer.ScriptedLoadableModule import *
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
# TMambaSeg
#


class TMambaSeg(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("ConeDent AI Metrix")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#TMambaSeg">module documentation</a>.
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

    # TMambaSeg1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="TMambaSeg",
        sampleName="TMambaSeg1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "TMambaSeg1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="TMambaSeg1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="TMambaSeg1",
    )

    # TMambaSeg2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="TMambaSeg",
        sampleName="TMambaSeg2",
        thumbnailFileName=os.path.join(iconsPath, "TMambaSeg2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="TMambaSeg2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="TMambaSeg2",
    )


#
# TMambaSegParameterNode
#


@parameterNodeWrapper
class TMambaSegParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode


#
# TMambaSegWidget
#


class TMambaSegWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
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

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # 界面布局
        # self.layout.addWidget(qt.QLabel("T-Mamba Segmentation Plugin"))


    def runInference(self, input_file: str, output_dir: str, log_widget: qt.QTextEdit) -> None:
        try:
            # 1. 预处理路径：替换反斜杠为斜杠
            input_file = input_file.replace("\\", "/")
            output_dir = output_dir.replace("\\", "/")
            win_script_path = "D:/AIbot/DentalCTSeg-main/T-Mamba/infer.sh"  # Windows 格式的脚本路径

            # 2. 转换所有路径到 WSL 格式
            # 转换脚本路径
            wsl_script_path = subprocess.run(
                ["wsl", "wslpath", "-u", win_script_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True
            ).stdout.strip()

            # 转换输入输出路径
            wsl_input_file = subprocess.run(
                ["wsl", "wslpath", "-u", input_file],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True
            ).stdout.strip()

            wsl_output_dir = subprocess.run(
                ["wsl", "wslpath", "-u", output_dir],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True
            ).stdout.strip()

            log_widget.append(f"WSL 脚本路径: {wsl_script_path}")
            log_widget.append(f"WSL 输入文件: {wsl_input_file}")
            log_widget.append(f"WSL 输出目录: {wsl_output_dir}")

            # 3. 检查脚本是否存在并具有执行权限
            check_script = subprocess.run(
                ["wsl", "test", "-f", wsl_script_path, "&&", "test", "-x", wsl_script_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if check_script.returncode != 0:
                log_widget.append(f"脚本检查失败: {wsl_script_path} 不存在或不可执行")
                if check_script.stderr:
                    log_widget.append(f"错误信息: {check_script.stderr}")
                return  # 提前退出，避免后续错误

            # 4. 确保激活 conda 环境并运行推理脚本
            import re

            # 创建带缓冲的进程对象
            process = subprocess.Popen(
                ["wsl", "bash", "-c",
                 f"source /home/pc/anaconda3/etc/profile.d/conda.sh && "
                 f"conda activate cbct && "
                 f"cd /mnt/d/AIbot/DentalCTSeg-main/T-Mamba && "
                 f"PYTHONUNBUFFERED=1 bash ./infer.sh '{wsl_input_file}' '{wsl_output_dir}'"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # 行缓冲模式（关键参数）
                encoding='utf-8',
                errors='replace'
            )

            # 实时处理输出流
            tqdm_pattern = re.compile(r"(\d+)%\|")  # 匹配tqdm进度格式
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break

                # 解析进度条（示例匹配：' 0%|...'）
                if match := tqdm_pattern.search(line):
                    percent = int(match.group(1))
                    if hasattr(self, 'progressBar'):  # 确保已初始化进度条控件
                        self.progressBar.setValue(percent)
                else:
                    # 只显示非进度信息的日志
                    clean_line = line.replace('\r', '').replace('\x1b[?25l', '').strip()
                    if clean_line:
                        log_widget.append(clean_line)
                        log_widget.ensureCursorVisible()  # 自动滚动

                qt.QApplication.processEvents()  # 保持UI响应


    def onApplyButton(self):
        """处理应用按钮点击"""
        if not self._parameterNode:
            slicer.util.errorDisplay("Parameter node is not initialized.")
            print("Parameter node is not initialized.")
            return

        input_file = self._parameterNode.GetParameter("inputFile")
        output_dir = self._parameterNode.GetParameter("outputDir")

        if not input_file or not output_dir:
            slicer.util.errorDisplay("Input file or output directory is not set.")
            print(f"Input file: {input_file}, Output directory: {output_dir}")  # Debug 输出
            return

        # 如果输入文件和输出目录都设置了，就可以进行推理
        self.runInference(input_file, output_dir, self.logText)
        print(f"Running inference with input: {input_file} and output: {output_dir}")  # Debug 输出

    def initializeParameterNode(self) -> None:
        if not self.logic:
            self.logic = TMambaSegLogic()
        self._parameterNode = self.logic.getParameterNode()
        if not self._parameterNode.inputFile:
            self._parameterNode.inputFile = ""
        if not self._parameterNode.outputDir:
            self._parameterNode.outputDir = ""


    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

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
        if self.logic:
            self.setParameterNode(self.logic.getParameterNode())
        else:
            print("Error: TMambaSegLogic is not initialized correctly.")

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: Optional[TMambaSegParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.thresholdedVolume:
            self.ui.applyButton.toolTip = _("Compute output volume")
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = _("Select input and output volume nodes")
            self.ui.applyButton.enabled = False


#
# TMambaSegLogic
#


class TMambaSegLogic(ScriptedLoadableModuleLogic):
    def __init__(self) -> None:
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return TMambaSegParameterNode(super().getParameterNode())


#
# TMambaSegTest
#


class TMambaSegTest(ScriptedLoadableModuleTest):
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
        self.test_TMambaSeg1()

    def test_TMambaSeg1(self):
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
        inputVolume = SampleData.downloadSample("TMambaSeg1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = TMambaSegLogic()

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
