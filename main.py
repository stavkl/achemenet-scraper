from bs4 import BeautifulSoup
import requests
import re
import math
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
}
base_url = 'http://www.achemenet.com'


def make_full_path(list_of_subpaths):
    for ix in range(0, len(list_of_subpaths)):
        list_of_subpaths[ix] = base_url + list_of_subpaths[ix]

    return list_of_subpaths


def get_pages_links_from_book(book_path):
    """
    This function extracts the paths of the pages in each book as well as generates paths to unseen pages (page numbers
    that go beyond the bar and need to be scrolled to be seen).
    This function does NOT extract a single page from books that have only one page, this is handles in the
    'get individual links' function
    :param book_path: a path to an individual book
    :return: a list of full paths of all the pages in the book
    """

    all_texts_links = []
    page2 = requests.get(book_path)
    doc = BeautifulSoup(page2.text, "html.parser")

    # Find the total number of items in the book
    info_items = doc.find_all(class_="info")
    total_num_of_texts = re.search(r'\d+', info_items[0].text).group()

    # Get the visible links of the PAGES from the first page, the rest will be generated later
    visible_links = doc.find_all(id="items-pager-div")
    for link in visible_links[0].find_all("a"):
        link_str = link.get('href')
        all_texts_links.append(link_str)

    # Figure out how many page-links are missing, if any
    num_of_missing_texts = int(total_num_of_texts) - 24 - 24*len(set(all_texts_links))
    # print(all_texts_links)
    if len(all_texts_links) > 0:
        tmp_link = all_texts_links[0]
        first_page_link = re.sub(r'/\d+/', '/1/', tmp_link, 1)
        all_texts_links.append(first_page_link)

    if num_of_missing_texts > 0:
        # Number of generated links should contain all and only the missing pages. Page #1 is generated separately
        num_of_pages_to_generate = math.ceil(num_of_missing_texts / 24)

        first_gen_page_ix = len(all_texts_links) + 1

        # last_gen_page_ix is intentionally +1 the actual page index,
        # so that when using range() we'll get the actual ix.
        last_gen_page_ix = first_gen_page_ix + num_of_pages_to_generate

        for i in range(first_gen_page_ix, last_gen_page_ix):

            replaced_link = re.sub(r'/\d+/', '/'+str(i)+'/', tmp_link, 1)
            all_texts_links.append(replaced_link)

    # Adding base url to all the pages
    all_texts_links = make_full_path(all_texts_links)
    return list(set(all_texts_links))


def get_book_links(achemenet_books_page):
    """
    :param achemenet_books_page: This should be the page of 'babylonian texts by publication'
    :return: a list of the links of the books
    """
    books_paths = []
    page = requests.get(achemenet_books_page)
    doc = BeautifulSoup(page.text, "html.parser")
    side_menu = doc.find_all(class_="parent")
    for link in side_menu[0].find_all("a"):
        link_str = link.get('href')
        full_link = base_url + link_str
        books_paths.append(full_link)
    return books_paths


def get_all_individual_links(achemenet_books_path, save_to_path):
    """
    Gets all the links (URL paths) to all the Babylonian texts in Achemenet. Note it only gets the links,
    not the content of the links - this step happens later

    :param achemenet_books_path: path to Achemenet website
    :param save_to_path: txt file path
    :return: a txt file with all the links for all the texts in Achemenet. This is the file that will be
    inspected to find diffs between scrapes
    """

    all_pages_links_l = []
    all_texts_links_l = []
    books_paths_l = get_book_links(achemenet_books_path)
    for book_path in books_paths_l:
        book_pages_l = get_pages_links_from_book(book_path)
        if len(book_pages_l) > 0:
            all_pages_links_l.extend(book_pages_l)
        else:
            all_pages_links_l.append(book_path)
        # print(book_path, len(book_pages_l))
    all_pages_links_l = make_full_path(all_pages_links_l)

    for page in set(all_pages_links_l):
        time.sleep(2000)
        page_content = requests.get(page, headers=headers)
        doc = BeautifulSoup(page_content.text, "html.parser")
        texts_links_block = doc.find_all(class_="item")
        for text_link in texts_links_block[0].find_all("a"):
            link_str = text_link.get('href')
            if str(link_str)[-1].isdigit():
                all_texts_links_l.append(str(link_str))
                print(str(link_str))

    with open(save_to_path, 'w') as f:
        for path in all_texts_links_l:
            f.write("%s\n" % path)
        f.write("\n")


def read_scrape_file(file_path):
    links = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            links.append(line)

    return links


def get_diff_between_scrapes(old_file, new_file):
    lines_old_l = read_scrape_file(old_file)
    lines_new_l = read_scrape_file(new_file)

    return [x for x in lines_new_l if x not in lines_old_l]


if __name__ == '__main__':
    # res = get_diff_between_scrapes('test_old.txt', 'test_new.txt')
    # for item in res:
    #     print(item)
    path = 'http://www.achemenet.com/en/tree/?/textual-sources/texts-by-publication/'
    get_all_individual_links(path, 'test_links_to_file.txt')

    # print(get_book_links('http://www.achemenet.com/en/tree/?/textual-sources/texts-by-publication'))

    # get_pages_links_from_book('http://www.achemenet.com/en/tree/?/textual-sources/texts-by-publication/Wunsch_IM/1/24/0#set')

    # page_content = requests.get('http://www.achemenet.com/en/tree/?/textual-sources/texts-by-publication/BE_81/1/24/0#set')
    # doc = BeautifulSoup(page_content.text, "html.parser")
    # texts_links_block = doc.find_all(class_="item")
    # i = 0
    # for text_link in texts_links_block[0].find_all("a"):
    #     link_str = text_link.get('href')
    #     if str(link_str)[-1].isdigit():
    #         i += 1
    #         print(link_str, i)



