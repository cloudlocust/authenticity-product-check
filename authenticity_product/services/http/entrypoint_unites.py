from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from authenticity_product.models import Article, User
from authenticity_product.schemas import (
    ArticleCreate,
    ArticleRead,
    GenerateListArticleQuery,
    ListArticlesOutType,
)
from authenticity_product.services.http.config import settings


articles_router = APIRouter()


@articles_router.post("/", response_model=ArticleRead)
def create_article(article: ArticleCreate, db: Session = Depends(settings.get_db)):
    """Create a new article."""
    dict_article = article.dict()
    if a := db.query(User).filter(User.email == dict_article["created_by_email"]).first():
        dict_article["owner_manufacturer_id"] = a.id.__str__()
    else:
        raise HTTPException(status_code=404, detail="User not found")
    dict_article.pop("created_by_email")
    dict_article["tag"] = dict_article.pop("status")
    db_article = Article(**dict_article)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return ArticleRead(
        id=db_article.id.__str__(),
        status=db_article.tag.__str__(),
        product_id=db_article.product_id.__str__(),
        created_by_id=db_article.owner_manufacturer_id.__str__(),
    )


@articles_router.get("/", response_model=ListArticlesOutType)
def read_articles(skip: int = 0, limit: int = 10, db: Session = Depends(settings.get_db)):
    """Read a list of articles."""
    articles = db.query(Article).offset(skip).limit(limit).all()
    list_articles = [
        ArticleRead(
            id=article.id.__str__(),
            status=article.tag.__str__(),
            product_id=article.product_id.__str__(),
            created_by_id=article.owner_manufacturer_id.__str__(),
        )
        for article in articles
    ]
    return ListArticlesOutType(articles=list_articles)


@articles_router.get("/{unite_id}", response_model=ArticleRead)
def read_article(unite_id: str, db: Session = Depends(settings.get_db)):
    article = db.query(Article).filter(Article.id == unite_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleRead(
        id=article.id.__str__(),
        status=article.tag.__str__(),
        product_id=article.product_id.__str__(),
        created_by_id=article.owner_manufacturer_id.__str__(),
    )


@articles_router.put("/{unite_id}", response_model=ArticleRead)
def update_article(unite_id: str, article: ArticleCreate, db: Session = Depends(settings.get_db)):
    """Update an article."""
    db_article = db.query(Article).filter(Article.id == unite_id).first()
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    for key, value in article.dict().items():
        setattr(db_article, key, value)
    db.commit()
    db.refresh(db_article)
    return ArticleRead(
        id=db_article.id.__str__(),
        status=db_article.tag.__str__(),
        product_id=db_article.product_id.__str__(),
        created_by_id=db_article.owner_manufacturer_id.__str__(),
    )


@articles_router.delete("/{unite_id}", response_model=ArticleRead)
def delete_article(unite_id: str, db: Session = Depends(settings.get_db)):
    """Delete an article."""
    db_article = db.query(Article).filter(Article.id == unite_id).first()
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(db_article)
    db.commit()
    return ArticleRead(
        id=db_article.id.__str__(),
        status=db_article.tag.__str__(),
        product_id=db_article.product_id.__str__(),
        created_by_id=db_article.owner_manufacturer_id.__str__(),
    )


@articles_router.post("/generate_articles", response_model=ListArticlesOutType)
def generate_articles_by_product(
    query: GenerateListArticleQuery, db: Session = Depends(settings.get_db)
):
    """Generate a list of articles by product."""
    dict_query = query.dict()
    if a := db.query(User).filter(User.email == dict_query["created_by_email"]).first():
        dict_query["created_by_id"] = a.id.__str__()
    else:
        raise HTTPException(status_code=404, detail="User not found")
    dict_query.pop("created_by_email")
    list_articles = [
        Article(
            product_id=dict_query["product_id"],
            owner_manufacturer_id=dict_query["created_by_id"],
            tag=dict_query["status"],
        )
        for i in range(query.nbr_unites)
    ]
    db.add_all(list_articles)
    db.commit()
    list_articles = [
        ArticleRead(
            id=article.id.__str__(),
            status=article.tag.__str__(),
            product_id=article.product_id.__str__(),
            created_by_id=article.owner_manufacturer_id.__str__(),
        )
        for article in list_articles
    ]
    return ListArticlesOutType(articles=list_articles)
