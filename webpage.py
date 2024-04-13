from functools import cached_property, lru_cache
import os
from pathlib import Path
from flask import Flask, render_template, send_file, redirect
import argparse

class MangaServed:
    def __init__(self, manga_path):
        self.manga_path = manga_path
    
    @cached_property
    def folders_list(self):
        return [x for x in Path(self.manga_path).iterdir() if x.is_dir()]
    
    @cached_property
    def folder_name_to_path(self):
        return {x.name: x for x in self.folders_list}
    
    @cached_property
    def folder_name_list(self):
        return sorted(list(self.folder_name_to_path.keys()))
    
    @cached_property
    def folder_name_and_url_tuple_list(self):
        return [(x, f'chapters/{x}') for x in self.folder_name_list]
    
    @cached_property
    def chapters_list(self):
        return self.folder_name_and_url_tuple_list
    
    @lru_cache
    def load_chapter_images(self, folder_name):
        folder_path = self.folder_name_to_path[folder_name]
        return dict([(x.name,x) for x in folder_path.iterdir() if x.is_file()])    
    
    def __len__(self):
        return len(self.folders_list)
    
    def __getitem__(self, key):
        return self.load_chapter_images(key)

def app_factory(manga_path):

    manga = MangaServed(manga_path)

    app = Flask(__name__)

    @app.route('/')
    def chapter_list():
        return render_template('chapter_list.html', 
                               chapters=[{'title':title,'url':url} for title,url in manga.chapters_list])
    
    @app.route('/chapters/<folder_name>')
    def chapter_link(folder_name):
        images = [{"title":k,"image":f'/images/{folder_name}/{k}'} for k,v in manga[folder_name].items()]
        print(images)
        return render_template('chapter_link.html', images=images, previous_url=f"/prev/{folder_name}", next_url=f"/next/{folder_name}")

    @app.route('/next/<folder_name>')
    def next_chapter(folder_name):
        idx = manga.folder_name_list.index(folder_name)
        if idx == len(manga)-1:
            return "No more chapters"
        return redirect(f'/chapters/{manga.folder_name_list[idx+1]}')
    
    @app.route('/prev/<folder_name>')
    def prev_chapter(folder_name):
        idx = manga.folder_name_list.index(folder_name)
        if idx == 0:
            return "No more chapters"
        return redirect(f'/chapters/{manga.folder_name_list[idx-1]}')
    
    @app.route('/images/<folder_name>/<image_name>')
    def image_link(folder_name, image_name):
        return send_file(manga[folder_name][image_name])
    return app

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('-m','--manga-path', type=str)
    args = parser.parse_args()
    app = app_factory(args.manga_path)
    app.run(port=args.port,host='0.0.0.0')
    