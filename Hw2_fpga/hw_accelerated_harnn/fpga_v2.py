from pynq import Overlay
import numpy as np
from pynq import allocate
from finn.util.data_packing import (
    finnpy_to_packed_bytearray,
    packed_bytearray_to_finnpy
)
import finn.custom_op.multithreshold as MT
from finn.core.datatype import DataType

class FPGA_V2():
    def __init__(self, bit_file_path):
        self.ol = Overlay(bit_file_path)
        self.dma=self.ol.axi_dma_0

        # declare input/output types and shapes for the accelerator
        # input FINN DataType
        self.idt = DataType.UINT2
        # normal, folded and packed input shapes
        self.ishape_normal = (1, 256)
        self.ishape_folded = (1, 4, 64)
        self.ishape_packed = (1, 4, 16)
        # output FINN DataType
        self.odt = DataType.INT32
        # normal, folded and packed output shapes
        self.oshape_normal = (1, 6)
        self.oshape_folded = (1, 1, 6)
        self.oshape_packed = (1, 1, 24)
        # allocate a PYNQ buffer for the packed input buffer
        self.ibuf_packed_device = allocate(shape=self.ishape_packed, dtype=np.uint8)
        # allocate a PYNQ buffer for the packed output buffer
        self.obuf_packed = allocate(shape=self.oshape_packed, dtype=np.uint8)
        self.mt_node_thresholds = np.asarray([[-0.00000762939453125, 0.00000762939453125]])
        self.multiply_node_const = 0.19533488154411316
        self.add_node_mat = np.asarray([0.7813395261764526, 0, 0, 0.7813395261764526, -0.3906697630882263, 0])

    def fpga_single_run(self, input):

        input = input.reshape(self.ishape_normal)
        input = MT.multithreshold(input, self.mt_node_thresholds)
        assert input.shape == self.ishape_normal
        ibuf_folded = input.reshape(self.ishape_folded)

        # pack the input buffer, reversing both SIMD dim and endianness
        ibuf_packed = finnpy_to_packed_bytearray(
            ibuf_folded, self.idt, reverse_endian=True, reverse_inner=True
        )
        # copy the packed data into the PYNQ buffer
        # TODO optimization: pack directly into the PYNQ buffer?
        np.copyto(self.ibuf_packed_device, ibuf_packed)

        # set up the DMA and wait until all transfers complete
        self.dma.sendchannel.transfer(self.ibuf_packed_device)
        self.dma.recvchannel.transfer(self.obuf_packed)
        self.dma.sendchannel.wait()
        self.dma.recvchannel.wait()

        # unpack the packed output buffer from accelerator
        obuf_folded = packed_bytearray_to_finnpy(
            self.obuf_packed, self.odt, self.oshape_folded, reverse_endian=True, reverse_inner=True
        )

        obuf_normal = obuf_folded.reshape(self.oshape_normal)
        obuf_normal = obuf_normal * self.multiply_node_const
        obuf_normal = obuf_normal + self.add_node_mat
        return obuf_normal
