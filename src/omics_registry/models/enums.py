import enum


class AssayType(str, enum.Enum):
    WGS = "WGS"
    WES = "WES"
    RNA_SEQ = "RNA-seq"
    ATAC_SEQ = "ATAC-seq"


class SampleType(str, enum.Enum):
    TUMOR = "tumor"
    NORMAL = "normal"


class AnalysisStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, enum.Enum):
    FASTQ = "FASTQ"
    BAM = "BAM"
    CRAM = "CRAM"
    VCF = "VCF"
    TSV = "TSV"
    OTHER = "OTHER"
