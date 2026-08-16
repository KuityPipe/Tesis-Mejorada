import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { IonicModule } from '@ionic/angular';

import { RecuperarPage } from './recuperar.page';
import { SharedModule } from '../shared/shared.module';

describe('RecuperarPage', () => {
  let component: RecuperarPage;
  let fixture: ComponentFixture<RecuperarPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [RecuperarPage],
      imports: [IonicModule.forRoot(), ReactiveFormsModule, HttpClientTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(RecuperarPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
