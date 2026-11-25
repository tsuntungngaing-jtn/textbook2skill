"""Local PDF evidence and optional Docling semantic parsing. No verified knowledge claims."""
import argparse
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def run(source, output, mode, start=1, end=None, dpi=144):
    import pymupdf as pm
    src,out=Path(source),Path(output)
    if mode not in ('native','semantic') or not 72<=dpi<=300:
        raise ValueError('Invalid mode or dpi')
    sha=digest(src)
    with pm.open(src) as pdf:
        if not pdf.is_pdf or pdf.needs_pass:
            raise ValueError('Readable PDF required')
        count=len(pdf)
        end=min(start+9,count) if end is None else end
        if not 1<=start<=end<=count:
            raise ValueError('Invalid inclusive physical page range')
        out.mkdir(parents=True,exist_ok=False)
        info={'source_sha256':sha,'source_name':src.name,'mode':mode,'start':start,'end':end,'page_count':count,'pymupdf_version':pm.VersionBind,'status':'INCOMPLETE','review_status':'UNREVIEWED'}
        dump(out/'manifest.json',info)
        if mode=='native':
            pages=[]
            for n in range(start,end+1):
                p=pdf[n-1]
                blocks=[{'bbox':b[:4],'text':b[4]} for b in p.get_text('blocks',sort=False) if b[6]==0]
                name=f'page-{n:05d}.png'
                p.get_pixmap(dpi=dpi,alpha=False).save(out/name)
                pages.append({'page':n,'printed_label':p.get_label() or None,'rotation':p.rotation,'width_pt':p.rect.width,'height_pt':p.rect.height,'blocks':blocks,'text':p.get_text(sort=False),'bitmap_boxes':[i['bbox'] for i in p.get_image_info()],'vector_count':len(p.get_drawings()),'render':name,'status':'UNREVIEWED'})
            dump(out/'pages.json',{'source_sha256':sha,'pages':pages})
            info.update(dpi=dpi,coordinate_system='unrotated MuPDF points, top-left; renders follow page rotation')
        else:
            semantic(src,out,start,end,info)
        if digest(src)!=sha:
            raise RuntimeError('Source changed; discard run')
        info['status']='PARSED_NOT_REVIEWED'
        dump(out/'manifest.json',info)
    return out

def semantic(src,out,start,end,info):
    from docling.datamodel.base_models import InputFormat, ConversionStatus
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling_core.types.doc import PictureItem, TableItem
    opts=PdfPipelineOptions()
    opts.do_ocr=True
    opts.do_table_structure=True
    opts.table_structure_options.mode=TableFormerMode.ACCURATE
    opts.do_formula_enrichment=True
    opts.generate_page_images=True
    opts.generate_picture_images=True
    opts.images_scale=2.0
    info.update(docling_version=version('docling'),docling_core_version=version('docling-core'),ocr=True,formula_enrichment=True,table_mode='ACCURATE',image_scale=2)
    dump(out/'manifest.json',info)
    converter=DocumentConverter(format_options={InputFormat.PDF:PdfFormatOption(pipeline_options=opts)})
    result=converter.convert(src,page_range=(start,end),raises_on_error=True)
    if result.status!=ConversionStatus.SUCCESS:
        raise RuntimeError(f'Docling non-success: {result.status}')
    doc=result.document
    dump(out/'document.json',doc.export_to_dict())
    (out/'document.md').write_text(doc.export_to_markdown(),encoding='utf-8')
    seen=set()
    elements=[]
    for idx,(item,level) in enumerate(doc.iterate_items()):
        prov=[{'page':p.page_no,'bbox':p.bbox.model_dump(mode='json')} for p in getattr(item,'prov',[])]
        seen.update(p['page'] for p in prov)
        record={'id':str(idx),'label':str(item.label),'provenance':prov,'status':'UNREVIEWED'}
        if isinstance(item,(PictureItem,TableItem)):
            img=item.get_image(doc)
            if img is not None:
                name=f'element-{idx:06d}.png'
                img.save(out/name)
                record['image']=name
            else:
                record['image_status']='MISSING_REVIEW_REQUIRED'
        elements.append(record)
    dump(out/'elements.json',{'elements':elements,'pages_with_element_provenance':sorted(seen),'pages_without_element_provenance':sorted(set(range(start,end+1))-seen)})
    if seen-set(range(start,end+1)):
        raise RuntimeError('Unexpected page provenance; review range mapping')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['native','semantic']); p.add_argument('source'); p.add_argument('output'); p.add_argument('--start',type=int,default=1); p.add_argument('--end',type=int); p.add_argument('--dpi',type=int,default=144)
    a=p.parse_args()
    print(run(a.source,a.output,a.mode,a.start,a.end,a.dpi))
